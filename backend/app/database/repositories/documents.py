"""Document and chunk persistence operations."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from typing import Any


def find_by_hash(connection: sqlite3.Connection, content_hash: str) -> sqlite3.Row | None:
    """Return a document with the supplied content hash, if present."""
    return connection.execute(
        """
        SELECT d.*, COUNT(c.id) AS chunk_count
        FROM documents AS d
        LEFT JOIN document_chunks AS c ON c.document_id = d.id
        WHERE d.content_hash = ?
        GROUP BY d.id
        """,
        (content_hash,),
    ).fetchone()


def insert_document(
    connection: sqlite3.Connection,
    document: dict[str, Any],
    chunks: Iterable[dict[str, Any]],
) -> None:
    """Insert one document and its chunks in the current transaction."""
    chunk_list = list(chunks)
    connection.execute(
        """
        INSERT INTO documents (
            id, original_filename, stored_filename, content_hash, file_type,
            byte_size, status, title, source_date, created_at, updated_at, error_code
        ) VALUES (
            :id, :original_filename, :stored_filename, :content_hash, :file_type,
            :byte_size, :status, :title, :source_date, :created_at, :updated_at, :error_code
        )
        """,
        document,
    )
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
        chunk_list,
    )
    filename = document.get("original_filename", "")
    connection.executemany(
        """
        INSERT INTO document_chunks_fts (chunk_id, document_id, filename, content)
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                c["id"],
                c["document_id"],
                filename,
                c["content"],
            )
            for c in chunk_list
        ],
    )


def count_documents(
    connection: sqlite3.Connection,
    *,
    query: str | None = None,
    status: str | None = None,
    file_type: str | None = None,
) -> int:
    """Return total number of documents matching the filters."""
    where_clauses: list[str] = []
    params: list[Any] = []
    if query:
        where_clauses.append("(d.original_filename LIKE ? OR d.title LIKE ?)")
        params.extend([f"%{query}%", f"%{query}%"])
    if status:
        where_clauses.append("d.status = ?")
        params.append(status)
    if file_type:
        where_clauses.append("d.file_type = ?")
        params.append(file_type.lower().lstrip("."))

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    sql = f"SELECT COUNT(*) FROM documents AS d {where_sql}"
    row = connection.execute(sql, params).fetchone()
    return int(row[0]) if row else 0


def list_documents(
    connection: sqlite3.Connection,
    *,
    query: str | None = None,
    status: str | None = None,
    file_type: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[sqlite3.Row]:
    """Return document metadata with chunk counts and optional filters/pagination."""
    where_clauses: list[str] = []
    params: list[Any] = []
    if query:
        where_clauses.append("(d.original_filename LIKE ? OR d.title LIKE ?)")
        params.extend([f"%{query}%", f"%{query}%"])
    if status:
        where_clauses.append("d.status = ?")
        params.append(status)
    if file_type:
        where_clauses.append("d.file_type = ?")
        params.append(file_type.lower().lstrip("."))

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    pagination_sql = ""
    if limit is not None:
        pagination_sql = "LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    sql = f"""
        SELECT d.*, COUNT(c.id) AS chunk_count
        FROM documents AS d
        LEFT JOIN document_chunks AS c ON c.document_id = d.id
        {where_sql}
        GROUP BY d.id
        ORDER BY d.created_at DESC
        {pagination_sql}
    """
    return list(connection.execute(sql, params).fetchall())


def get_document(connection: sqlite3.Connection, document_id: str) -> sqlite3.Row | None:
    """Return document metadata with its chunk count."""
    return connection.execute(
        """
        SELECT d.*, COUNT(c.id) AS chunk_count
        FROM documents AS d
        LEFT JOIN document_chunks AS c ON c.document_id = d.id
        WHERE d.id = ?
        GROUP BY d.id
        """,
        (document_id,),
    ).fetchone()


def get_chunks(connection: sqlite3.Connection, document_id: str) -> list[sqlite3.Row]:
    """Return all chunks for one document in stable order."""
    return list(
        connection.execute(
            "SELECT * FROM document_chunks WHERE document_id = ? ORDER BY chunk_index",
            (document_id,),
        ).fetchall()
    )


def mark_deleting(connection: sqlite3.Connection, document_id: str) -> sqlite3.Row | None:
    """Mark a document as deleting and return its metadata."""
    row = connection.execute(
        "SELECT * FROM documents WHERE id = ?",
        (document_id,),
    ).fetchone()
    if row is None:
        return None
    connection.execute(
        """
        UPDATE documents
        SET status = 'deleting', updated_at = datetime('now')
        WHERE id = ?
        """,
        (document_id,),
    )
    return row


def delete_document(connection: sqlite3.Connection, document_id: str) -> None:
    """Delete a document; foreign keys remove its chunks."""
    connection.execute("DELETE FROM document_chunks_fts WHERE document_id = ?", (document_id,))
    connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))


def document_storage_path(settings: Any, row: sqlite3.Row):
    """Resolve a stored filename under the app-owned files directory."""
    return settings.files_dir / row["stored_filename"]
