"""Vector-index and full-text index maintenance operations."""

from __future__ import annotations

from app.core.config import Settings
from app.database.connection import connect, initialize_database
from app.retrieval.embeddings import EmbeddingProvider, get_embedding_provider
from app.retrieval.vector_store import ChromaVectorStore


def rebuild_index_from_sqlite(
    settings: Settings,
    *,
    embedding_provider: EmbeddingProvider | None = None,
    vector_store: ChromaVectorStore | None = None,
) -> int:
    """Recreate vector and lexical records for all ready SQLite chunks."""
    initialize_database(settings)
    with connect(settings) as connection:
        connection.execute("DELETE FROM document_chunks_fts")
        connection.execute(
            """
            INSERT INTO document_chunks_fts (chunk_id, document_id, filename, content)
            SELECT c.id, c.document_id, d.original_filename, c.content
            FROM document_chunks AS c
            JOIN documents AS d ON d.id = c.document_id
            WHERE d.status = 'ready'
            """
        )
        rows = connection.execute(
            """
            SELECT c.*, d.file_type
            FROM document_chunks AS c
            JOIN documents AS d ON d.id = c.document_id
            WHERE d.status = 'ready'
            ORDER BY c.document_id, c.chunk_index
            """
        ).fetchall()

    if not rows:
        return 0
    provider = embedding_provider or get_embedding_provider(settings.embedding_model)
    store = vector_store or ChromaVectorStore(settings)
    store.upsert(
        [row["id"] for row in rows],
        provider.embed_documents([row["content"] for row in rows]),
        [row["content"] for row in rows],
        [
            {
                "document_id": row["document_id"],
                "chunk_index": row["chunk_index"],
                "file_type": row["file_type"],
            }
            for row in rows
        ],
    )
    return len(rows)
