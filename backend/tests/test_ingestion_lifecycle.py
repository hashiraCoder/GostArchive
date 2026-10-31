"""Comprehensive test suite for Phase 1: Ingestion & Indexing Reliability."""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.errors import ErrorCode, GhostArchiveException
from app.database.connection import connect, initialize_database
from app.services.document_service import recover_interrupted_documents
from app.services.search_service import search_documents


def test_upload_small_pdf_rejected_as_unsupported(client: TestClient) -> None:
    """PDF format returns 422 until Phase 2 extraction engine is implemented."""
    res = client.post(
        "/api/documents",
        files={"file": ("sample.pdf", b"%PDF-1.4 sample content", "application/pdf")},
    )
    assert res.status_code == 422
    data = res.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "Only .txt and .md files are supported" in data["error"]["message"]


def test_upload_large_pdf_rejected(client: TestClient, temp_settings: Settings) -> None:
    """Large PDF exceeding limits is rejected with appropriate error envelope."""
    temp_settings.upload_max_bytes = 100
    res = client.post(
        "/api/documents",
        files={"file": ("large.pdf", b"%PDF-1.4 " * 50, "application/pdf")},
    )
    # Either 422 (unsupported) or 413 (size limit)
    assert res.status_code in (413, 422)
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_upload_docx_rejected_as_unsupported(client: TestClient) -> None:
    """DOCX format returns 422 until dedicated extractor is integrated."""
    docx_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    res = client.post(
        "/api/documents",
        files={"file": ("notes.docx", b"PK\x03\x04 fake docx binary", docx_mime)},
    )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_upload_unsupported_binary_formats(client: TestClient) -> None:
    """Arbitrary unsupported formats (.exe, .bin, .py, .json) are rejected."""
    for filename in ("app.exe", "data.bin", "script.py", "records.json"):
        res = client.post(
            "/api/documents",
            files={"file": (filename, b"test content", "application/octet-stream")},
        )
        assert res.status_code == 422, f"Expected 422 for {filename}"
        assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_upload_corrupted_non_utf8_text(client: TestClient) -> None:
    """Binary garbage with .txt extension fails UTF-8 decoding."""
    res = client.post(
        "/api/documents",
        files={"file": ("corrupt.txt", b"\x80\x81\xfe\xff invalid utf8", "text/plain")},
    )
    assert res.status_code == 422
    assert "valid UTF-8 text" in res.json()["error"]["message"]


def test_upload_empty_document(client: TestClient) -> None:
    """Empty files or whitespace-only documents are rejected."""
    for empty_bytes in (b"", b"   \r\n\t  \n  "):
        res = client.post(
            "/api/documents",
            files={"file": ("empty.txt", empty_bytes, "text/plain")},
        )
        assert res.status_code == 422
        assert "no extractable text" in res.json()["error"]["message"]


def test_upload_embedding_failure_records_error_status(
    client: TestClient, temp_settings: Settings, monkeypatch
) -> None:
    """When embedding model throws an error, document status is recorded as 'error'."""
    mock_provider = MagicMock()
    mock_provider.embed_documents.side_effect = GhostArchiveException(
        ErrorCode.EMBEDDING_UNAVAILABLE, "Embedding service failed.", 503
    )

    from app.services import document_service

    monkeypatch.setattr(document_service, "get_embedding_provider", lambda _: mock_provider)

    res = client.post(
        "/api/documents",
        files={"file": ("failing.txt", b"Valid text that will fail embedding.", "text/plain")},
    )
    assert res.status_code == 503

    with sqlite3.connect(temp_settings.db_path) as conn:
        conn.row_factory = sqlite3.Row
        sql = "SELECT * FROM documents WHERE original_filename = 'failing.txt'"
        row = conn.execute(sql).fetchone()
        assert row is not None
        assert row["status"] == "error"
        assert row["error_code"] == "EMBEDDING_UNAVAILABLE"


def test_upload_vector_store_failure_records_error_status(
    client: TestClient, temp_settings: Settings, monkeypatch
) -> None:
    """When vector store upsert throws an error, document status is recorded as 'error'."""
    from app.services import document_service

    class BrokenVectorStore:
        def __init__(self, *args, **kwargs):
            pass

        def upsert(self, *args, **kwargs):
            raise RuntimeError("Chroma write disk full simulation")

        def delete(self, *args, **kwargs):
            pass

    monkeypatch.setattr(document_service, "ChromaVectorStore", BrokenVectorStore)

    res = client.post(
        "/api/documents",
        files={"file": ("vector_fail.txt", b"Valid text that fails vector upsert.", "text/plain")},
    )
    assert res.status_code == 500

    with sqlite3.connect(temp_settings.db_path) as conn:
        conn.row_factory = sqlite3.Row
        sql = "SELECT * FROM documents WHERE original_filename = 'vector_fail.txt'"
        row = conn.execute(sql).fetchone()
        assert row is not None
        assert row["status"] == "error"
        assert row["error_code"] == "STORE_ERROR"


def test_backend_restart_recovers_interrupted_documents(temp_settings: Settings) -> None:
    """Documents left in 'processing' during crash are recovered to 'error' on restart."""
    initialize_database(temp_settings)
    with connect(temp_settings) as conn:
        conn.execute(
            """
            INSERT INTO documents (
                id, original_filename, stored_filename, content_hash, file_type,
                byte_size, status, title, source_date, created_at, updated_at, error_code
            ) VALUES (
                'doc-interrupted', 'crashed.txt', 'crashed.txt', 'hash-crash-1', 'txt',
                100, 'processing', NULL, NULL, '2026-10-31T00:00:00Z', '2026-10-31T00:00:00Z', NULL
            )
            """
        )

    recovered = recover_interrupted_documents(temp_settings)
    assert recovered == 1

    with connect(temp_settings) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM documents WHERE id = 'doc-interrupted'").fetchone()
        assert row["status"] == "error"
        assert row["error_code"] == "INTERRUPTED"


def test_retry_after_failure_reingests_cleanly(client: TestClient, temp_settings: Settings) -> None:
    """Re-uploading a file whose previous run failed cleans up the old record and succeeds."""
    content = b"Content for document that will fail then retry successfully."
    initialize_database(temp_settings)
    import hashlib

    content_hash = hashlib.sha256(content).hexdigest()
    with connect(temp_settings) as conn:
        conn.execute(
            """
            INSERT INTO documents (
                id, original_filename, stored_filename, content_hash, file_type,
                byte_size, status, title, source_date, created_at, updated_at, error_code
            ) VALUES (
                'failed-attempt-id', 'retry_doc.txt', 'failed-attempt-id.txt', ?, 'txt',
                100, 'error', NULL, NULL, '2026-10-31T00:00:00Z',
                '2026-10-31T00:00:00Z', 'STORE_ERROR'
            )
            """,
            (content_hash,),
        )

    # Re-upload the same file content
    res = client.post(
        "/api/documents",
        files={"file": ("retry_doc.txt", content, "text/plain")},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["duplicate"] is False
    assert data["document"]["status"] == "ready"
    assert data["document"]["id"] != "failed-attempt-id"


def test_ready_document_is_immediately_searchable(
    client: TestClient, temp_settings: Settings
) -> None:
    """When ingestion finishes with 'ready', it is immediately searchable in hybrid retrieval."""
    unique_marker = "NyquistRateVerificationMarker99"
    content = f"Sampling theory experiment with {unique_marker} in the text.".encode()

    res = client.post(
        "/api/documents",
        files={"file": ("searchable.txt", content, "text/plain")},
    )
    assert res.status_code == 201
    assert res.json()["document"]["status"] == "ready"

    # Search immediately
    hits = search_documents(temp_settings, unique_marker, top_k=5)
    assert len(hits) >= 1
    assert unique_marker in hits[0]["text"]
