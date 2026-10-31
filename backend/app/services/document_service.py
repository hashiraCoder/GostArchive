"""Document ingestion and deletion orchestration."""

from __future__ import annotations

import hashlib
import logging
import re
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import UploadFile

from app.core.config import Settings
from app.core.errors import ErrorCode, GhostArchiveException
from app.database.connection import connect, initialize_database
from app.database.repositories.documents import (
    count_documents,
    delete_document,
    document_storage_path,
    find_by_hash,
    get_chunks,
    get_document,
    insert_document,
    list_documents,
    mark_deleting,
)
from app.ingestion.normalize import chunk_text, normalize_text
from app.retrieval.embeddings import EmbeddingProvider, get_embedding_provider
from app.retrieval.vector_store import ChromaVectorStore

logger = logging.getLogger("ghostarchive.documents")

ALLOWED_EXTENSIONS = {".txt", ".md"}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _safe_filename(filename: str | None) -> str:
    candidate = Path(filename or "untitled").name
    return re.sub(r"[^\w .-]", "_", candidate).strip() or "untitled"


async def ingest_upload(
    settings: Settings,
    upload: UploadFile,
    *,
    embedding_provider: EmbeddingProvider | None = None,
    vector_store: ChromaVectorStore | None = None,
) -> tuple[dict, bool]:
    """Validate, persist, normalize, chunk, and record a text upload."""
    filename = _safe_filename(upload.filename)
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise GhostArchiveException(
            ErrorCode.VALIDATION_ERROR,
            "Only .txt and .md files are supported.",
            422,
        )

    content = await upload.read(settings.upload_max_bytes + 1)
    if len(content) > settings.upload_max_bytes:
        raise GhostArchiveException(
            ErrorCode.VALIDATION_ERROR,
            "The uploaded file exceeds the configured size limit.",
            413,
        )
    content_hash = hashlib.sha256(content).hexdigest()
    initialize_database(settings)
    with connect(settings) as connection:
        existing = find_by_hash(connection, content_hash)
        if existing is not None:
            if existing["status"] == "error":
                # Clear previous failed attempt to enable clean retry
                delete_document(connection, existing["id"])
                (settings.files_dir / existing["stored_filename"]).unlink(missing_ok=True)
            else:
                return _document_response(existing), True

    try:
        text = normalize_text(content.decode("utf-8-sig"))
    except UnicodeDecodeError as exc:
        raise GhostArchiveException(
            ErrorCode.VALIDATION_ERROR,
            "The file must contain valid UTF-8 text.",
            422,
        ) from exc
    if not text:
        raise GhostArchiveException(
            ErrorCode.VALIDATION_ERROR,
            "The uploaded file contains no extractable text.",
            422,
        )
    if len(text) > settings.extracted_text_max_chars:
        raise GhostArchiveException(
            ErrorCode.VALIDATION_ERROR,
            "The extracted text exceeds the configured character limit.",
            422,
        )

    document_id = str(uuid.uuid4())
    stored_filename = f"{uuid.uuid4()}{extension}"
    settings.files_dir.mkdir(parents=True, exist_ok=True)
    storage_path = settings.files_dir / stored_filename
    chunks = chunk_text(text)
    now = _utc_now()
    document = {
        "id": document_id,
        "original_filename": filename,
        "stored_filename": stored_filename,
        "content_hash": content_hash,
        "file_type": extension[1:],
        "byte_size": len(content),
        "status": "processing",
        "title": None,
        "source_date": None,
        "created_at": now,
        "updated_at": now,
        "error_code": None,
    }
    chunk_rows = [
        {
            "id": f"{document_id}:{chunk.index}:{chunk.start_char}-{chunk.end_char}",
            "document_id": document_id,
            "chunk_index": chunk.index,
            "content": chunk.content,
            "page_number": None,
            "start_char": chunk.start_char,
            "end_char": chunk.end_char,
            "created_at": now,
        }
        for chunk in chunks
    ]

    try:
        storage_path.write_bytes(content)
        try:
            with connect(settings) as connection:
                insert_document(connection, document, chunk_rows)
        except sqlite3.IntegrityError:
            storage_path.unlink(missing_ok=True)
            with connect(settings) as connection:
                existing = find_by_hash(connection, content_hash)
                if existing is not None:
                    return _document_response(existing), True
            raise

        provider = embedding_provider or get_embedding_provider(settings.embedding_model)
        store = vector_store or ChromaVectorStore(settings)
        embeddings = provider.embed_documents([chunk["content"] for chunk in chunk_rows])
        store.upsert(
            [chunk["id"] for chunk in chunk_rows],
            embeddings,
            [chunk["content"] for chunk in chunk_rows],
            [
                {
                    "document_id": document_id,
                    "chunk_index": chunk["chunk_index"],
                    "file_type": extension[1:],
                }
                for chunk in chunk_rows
            ],
        )
        with connect(settings) as connection:
            connection.execute(
                "UPDATE documents SET status = 'ready', updated_at = ? WHERE id = ?",
                (_utc_now(), document_id),
            )
            row = get_document(connection, document_id)
            if row is None:
                raise RuntimeError("Inserted document could not be reloaded")
            return _document_response(row), False
    except GhostArchiveException as exc:
        if "store" in locals():
            store.delete([chunk["id"] for chunk in chunk_rows])
        with connect(settings) as connection:
            connection.execute(
                "UPDATE documents SET status = 'error', error_code = ?, updated_at = ? "
                "WHERE id = ?",
                (str(exc.code), _utc_now(), document_id),
            )
        raise
    except Exception as exc:
        if "store" in locals():
            store.delete([chunk["id"] for chunk in chunk_rows])
        with connect(settings) as connection:
            connection.execute(
                "UPDATE documents SET status = 'error', error_code = 'STORE_ERROR', "
                "updated_at = ? WHERE id = ?",
                (_utc_now(), document_id),
            )
        raise GhostArchiveException(
            ErrorCode.STORE_ERROR,
            "The document could not be stored.",
            500,
            retryable=True,
        ) from exc


def _document_response(row) -> dict:
    """Convert a SQLite row to the public document response shape."""
    row_keys = tuple(row.keys()) if hasattr(row, "keys") else ()
    return {
        "id": row["id"],
        "filename": row["original_filename"],
        "file_type": row["file_type"],
        "byte_size": row["byte_size"],
        "status": row["status"],
        "chunk_count": row["chunk_count"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "error_code": row["error_code"] if "error_code" in row_keys else None,
    }


def recover_interrupted_documents(settings: Settings) -> int:
    """Recover documents left in 'processing' or 'deleting' state after an unclean restart."""
    initialize_database(settings)
    with connect(settings) as connection:
        cursor = connection.execute(
            """
            UPDATE documents
            SET status = 'error', error_code = 'INTERRUPTED', updated_at = ?
            WHERE status IN ('processing', 'deleting')
            """,
            (_utc_now(),),
        )
        recovered = cursor.rowcount
        if recovered > 0:
            logger.warning("Recovered %d interrupted documents to error state", recovered)
        return recovered


def get_documents(
    settings: Settings,
    *,
    query: str | None = None,
    status: str | None = None,
    file_type: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """List stored document metadata with optional filtering and pagination."""
    initialize_database(settings)
    with connect(settings) as connection:
        total = count_documents(
            connection,
            query=query,
            status=status,
            file_type=file_type,
        )
        rows = list_documents(
            connection,
            query=query,
            status=status,
            file_type=file_type,
            limit=limit,
            offset=offset,
        )
        return [_document_response(row) for row in rows], total


def get_document_by_id(settings: Settings, document_id: str) -> dict | None:
    """Return one document's metadata."""
    initialize_database(settings)
    with connect(settings) as connection:
        row = get_document(connection, document_id)
        return _document_response(row) if row else None


def remove_document(settings: Settings, document_id: str) -> bool:
    """Idempotently delete a document row, stored source file, and vector chunks."""
    initialize_database(settings)
    chunk_ids: list[str] = []
    with connect(settings) as connection:
        chunks = get_chunks(connection, document_id)
        chunk_ids = [chunk["id"] for chunk in chunks]
        row = mark_deleting(connection, document_id)
        if row is not None:
            storage_path = document_storage_path(settings, row)
            storage_path.unlink(missing_ok=True)

    if chunk_ids:
        try:
            ChromaVectorStore(settings).delete(chunk_ids)
        except Exception as exc:
            logger.warning(
                "Could not delete Chroma vectors for document %s: %s",
                document_id,
                exc,
            )

    with connect(settings) as connection:
        delete_document(connection, document_id)

    return True


def bulk_remove_documents(settings: Settings, document_ids: list[str]) -> tuple[list[dict], int]:
    """Idempotently delete multiple documents, returning per-document results."""
    results: list[dict] = []
    total_deleted = 0
    for doc_id in document_ids:
        try:
            remove_document(settings, doc_id)
            results.append({"id": doc_id, "success": True, "error": None})
            total_deleted += 1
        except Exception as exc:
            logger.warning("Failed to delete document %s: %s", doc_id, exc)
            results.append({"id": doc_id, "success": False, "error": str(exc)})
    return results, total_deleted


def rechunk_document(
    settings: Settings,
    document_id: str,
    *,
    embedding_provider: EmbeddingProvider | None = None,
    vector_store: ChromaVectorStore | None = None,
) -> dict:
    """Re-normalize, re-chunk, and re-embed an existing document from its stored source file."""
    initialize_database(settings)
    with connect(settings) as connection:
        doc = get_document(connection, document_id)
        if not doc:
            raise GhostArchiveException(ErrorCode.NOT_FOUND, "Document not found.", 404)
        storage_path = document_storage_path(settings, doc)
        if not storage_path.exists():
            raise GhostArchiveException(ErrorCode.NOT_FOUND, "Source file not found on disk.", 404)

        content = storage_path.read_bytes()
        text = normalize_text(content.decode("utf-8-sig", errors="replace"))
        chunks = chunk_text(text)
        now = _utc_now()

        old_chunks = get_chunks(connection, document_id)
        old_chunk_ids = [c["id"] for c in old_chunks]

        chunk_rows = [
            {
                "id": f"{document_id}:{chunk.index}:{chunk.start_char}-{chunk.end_char}",
                "document_id": document_id,
                "chunk_index": chunk.index,
                "content": chunk.content,
                "page_number": None,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "created_at": now,
            }
            for chunk in chunks
        ]

        connection.execute("DELETE FROM document_chunks_fts WHERE document_id = ?", (document_id,))
        connection.execute("DELETE FROM document_chunks WHERE document_id = ?", (document_id,))
        connection.executemany(
            """
            INSERT INTO document_chunks (
                id, document_id, chunk_index, content, page_number,
                start_char, end_char, created_at
            ) VALUES (
                :id, :document_id, :chunk_index, :content, :page_number,
                :start_char, :end_char, :created_at
            )
            """,
            chunk_rows,
        )
        connection.executemany(
            """
            INSERT INTO document_chunks_fts (chunk_id, document_id, filename, content)
            VALUES (?, ?, ?, ?)
            """,
            [
                (c["id"], c["document_id"], doc["original_filename"], c["content"])
                for c in chunk_rows
            ],
        )
        connection.execute(
            "UPDATE documents SET status = 'ready', error_code = NULL, updated_at = ? WHERE id = ?",
            (now, document_id),
        )

    store = vector_store or ChromaVectorStore(settings)
    if old_chunk_ids:
        try:
            store.delete(old_chunk_ids)
        except Exception as exc:
            logger.warning("Could not delete old Chroma vectors during rechunk: %s", exc)

    provider = embedding_provider or get_embedding_provider(settings.embedding_model)
    embeddings = provider.embed_documents([chunk["content"] for chunk in chunk_rows])
    store.upsert(
        [chunk["id"] for chunk in chunk_rows],
        embeddings,
        [chunk["content"] for chunk in chunk_rows],
        [
            {
                "document_id": document_id,
                "chunk_index": chunk["chunk_index"],
                "file_type": doc["file_type"],
            }
            for chunk in chunk_rows
        ],
    )
    with connect(settings) as connection:
        updated_doc = get_document(connection, document_id)
        if not updated_doc:
            raise RuntimeError("Document could not be reloaded after rechunking")
        return _document_response(updated_doc)
