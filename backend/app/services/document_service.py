"""Document ingestion and deletion orchestration."""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import UploadFile

from app.core.config import Settings
from app.core.errors import ErrorCode, GhostArchiveException
from app.database.connection import connect, initialize_database
from app.database.repositories.documents import (
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
        with connect(settings) as connection:
            insert_document(connection, document, chunk_rows)
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
    except GhostArchiveException:
        if "store" in locals():
            store.delete([chunk["id"] for chunk in chunk_rows])
        with connect(settings) as connection:
            delete_document(connection, document_id)
        storage_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        if "store" in locals():
            store.delete([chunk["id"] for chunk in chunk_rows])
        with connect(settings) as connection:
            delete_document(connection, document_id)
        storage_path.unlink(missing_ok=True)
        raise GhostArchiveException(
            ErrorCode.STORE_ERROR,
            "The document could not be stored.",
            500,
            retryable=True,
        ) from exc


def _document_response(row) -> dict:
    """Convert a SQLite row to the public document response shape."""
    return {
        "id": row["id"],
        "filename": row["original_filename"],
        "file_type": row["file_type"],
        "byte_size": row["byte_size"],
        "status": row["status"],
        "chunk_count": row["chunk_count"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def get_documents(settings: Settings) -> list[dict]:
    """List stored document metadata."""
    initialize_database(settings)
    with connect(settings) as connection:
        return [_document_response(row) for row in list_documents(connection)]


def get_document_by_id(settings: Settings, document_id: str) -> dict | None:
    """Return one document's metadata."""
    initialize_database(settings)
    with connect(settings) as connection:
        row = get_document(connection, document_id)
        return _document_response(row) if row else None


def remove_document(settings: Settings, document_id: str) -> bool:
    """Delete a document row and its stored source file."""
    initialize_database(settings)
    with connect(settings) as connection:
        row = mark_deleting(connection, document_id)
        if row is None:
            return False
        storage_path = document_storage_path(settings, row)
    storage_path.unlink(missing_ok=True)
    with connect(settings) as connection:
        chunks = get_chunks(connection, document_id)
        ChromaVectorStore(settings).delete([chunk["id"] for chunk in chunks])
        delete_document(connection, document_id)
    return True
