"""Tests for Phase 2 document ingestion and persistence."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings


def test_upload_txt_persists_ready_document(client: TestClient, temp_settings: Settings) -> None:
    response = client.post(
        "/api/documents",
        files={
            "file": (
                "journal.txt",
                ("First paragraph. " * 45 + "\n\n" + "Second paragraph. " * 45).encode(),
                "text/plain",
            )
        },
    )

    assert response.status_code == 201
    data = response.json()
    document = data["document"]
    assert document["status"] == "ready"
    assert document["file_type"] == "txt"
    assert document["chunk_count"] == 2
    assert data["duplicate"] is False

    with sqlite3.connect(temp_settings.db_path) as connection:
        row = connection.execute(
            "SELECT status, original_filename, stored_filename FROM documents WHERE id = ?",
            (document["id"],),
        ).fetchone()
    assert row is not None
    assert row[0] == "ready"
    assert row[1] == "journal.txt"
    assert Path(temp_settings.files_dir, row[2]).exists()


def test_upload_invalid_extension_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/documents",
        files={"file": ("archive.pdf", b"not a pdf", "application/pdf")},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_upload_oversized_file_returns_413(client: TestClient, temp_settings: Settings) -> None:
    temp_settings.upload_max_bytes = 4
    response = client.post(
        "/api/documents",
        files={"file": ("large.txt", b"12345", "text/plain")},
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_duplicate_content_returns_existing_document(
    client: TestClient,
) -> None:
    payload = {"file": ("first.txt", b"same content", "text/plain")}
    first = client.post("/api/documents", files=payload)
    duplicate = client.post(
        "/api/documents",
        files={"file": ("renamed.md", b"same content", "text/markdown")},
    )

    assert first.status_code == 201
    assert duplicate.status_code == 201
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["document"]["id"] == first.json()["document"]["id"]
    assert duplicate.json()["document"]["filename"] == "first.txt"


def test_list_and_delete_document(client: TestClient, temp_settings: Settings) -> None:
    created = client.post(
        "/api/documents",
        files={"file": ("note.md", b"# A note", "text/markdown")},
    )
    document_id = created.json()["document"]["id"]

    listed = client.get("/api/documents")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == document_id

    deleted = client.delete(f"/api/documents/{document_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/documents/{document_id}").status_code == 404

    # Idempotent: repeating delete returns 204 without error
    second_deleted = client.delete(f"/api/documents/{document_id}")
    assert second_deleted.status_code == 204

    # Deleting arbitrary non-existent ID also returns 204
    non_existent = client.delete("/api/documents/non-existent-id-12345")
    assert non_existent.status_code == 204

    with sqlite3.connect(temp_settings.db_path) as connection:
        assert (
            connection.execute("SELECT 1 FROM documents WHERE id = ?", (document_id,)).fetchone()
            is None
        )
        assert (
            connection.execute(
                "SELECT 1 FROM document_chunks WHERE document_id = ?", (document_id,)
            ).fetchone()
            is None
        )
    assert list(temp_settings.files_dir.iterdir()) == []


def test_empty_text_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/documents",
        files={"file": ("empty.txt", b"\n\r\n", "text/plain")},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_document_filtering_and_pagination(client: TestClient) -> None:
    # Ingest 3 documents
    client.post(
        "/api/documents",
        files={"file": ("alpha_report.txt", b"Alpha content for research.", "text/plain")},
    )
    client.post(
        "/api/documents",
        files={"file": ("beta_notes.md", b"# Beta notes about drainage.", "text/markdown")},
    )
    client.post(
        "/api/documents",
        files={"file": ("gamma_report.txt", b"Gamma report content.", "text/plain")},
    )

    # Test filename query filter
    res_query = client.get("/api/documents", params={"query": "report"})
    assert res_query.status_code == 200
    assert res_query.json()["total"] == 2
    filenames = [doc["filename"] for doc in res_query.json()["items"]]
    assert "alpha_report.txt" in filenames
    assert "gamma_report.txt" in filenames
    assert "beta_notes.md" not in filenames

    # Test file_type filter
    res_md = client.get("/api/documents", params={"file_type": "md"})
    assert res_md.status_code == 200
    assert res_md.json()["total"] == 1
    assert res_md.json()["items"][0]["filename"] == "beta_notes.md"

    # Test status filter
    res_status = client.get("/api/documents", params={"status": "ready"})
    assert res_status.status_code == 200
    assert res_status.json()["total"] == 3

    # Test pagination
    res_page1 = client.get("/api/documents", params={"limit": 2, "offset": 0})
    assert res_page1.status_code == 200
    assert res_page1.json()["total"] == 3
    assert len(res_page1.json()["items"]) == 2

    res_page2 = client.get("/api/documents", params={"limit": 2, "offset": 2})
    assert res_page2.status_code == 200
    assert res_page2.json()["total"] == 3
    assert len(res_page2.json()["items"]) == 1


def test_bulk_deletion(client: TestClient) -> None:
    d1 = client.post(
        "/api/documents",
        files={"file": ("bulk1.txt", b"Content bulk 1", "text/plain")},
    ).json()["document"]
    d2 = client.post(
        "/api/documents",
        files={"file": ("bulk2.txt", b"Content bulk 2", "text/plain")},
    ).json()["document"]

    # Delete both + a non-existent ID (partial/idempotent check)
    res = client.post(
        "/api/documents/bulk-delete",
        json={"document_ids": [d1["id"], d2["id"], "non-existent-id"]},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_deleted"] == 3  # All handled idempotently
    assert len(data["results"]) == 3
    assert all(r["success"] is True for r in data["results"])

    # Verify they are gone
    listed = client.get("/api/documents")
    assert listed.status_code == 200
    remaining_ids = [doc["id"] for doc in listed.json()["items"]]
    assert d1["id"] not in remaining_ids
    assert d2["id"] not in remaining_ids
