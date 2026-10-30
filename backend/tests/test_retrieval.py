"""Tests for Phase 3 semantic retrieval."""

from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.database.connection import connect, initialize_database
from app.retrieval.embeddings import get_embedding_provider
from app.retrieval.vector_store import ChromaVectorStore
from app.services.document_service import ingest_upload
from app.services.index_service import rebuild_index_from_sqlite
from app.services.search_service import search_documents


class FakeEmbeddingProvider:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text))] for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text))]


class FakeVectorStore:
    def __init__(self) -> None:
        self.records: dict[str, dict[str, Any]] = {}
        self.last_top_k: int | None = None
        self.last_document_ids: list[str] | None = None

    def upsert(self, ids, embeddings, documents, metadatas) -> None:
        for chunk_id, embedding, document, metadata in zip(
            ids, embeddings, documents, metadatas, strict=True
        ):
            self.records[chunk_id] = {
                "embedding": embedding,
                "document": document,
                "metadata": metadata,
            }

    def query(self, embedding, top_k, document_ids=None):
        self.last_top_k = top_k
        self.last_document_ids = list(document_ids or [])
        records = [
            (chunk_id, record)
            for chunk_id, record in self.records.items()
            if not document_ids or record["metadata"]["document_id"] in document_ids
        ]
        records = records[:top_k]
        return {
            "ids": [[chunk_id for chunk_id, _ in records]],
            "distances": [[0.1 for _ in records]],
        }

    def delete(self, ids) -> None:
        for chunk_id in ids:
            self.records.pop(chunk_id, None)


def _insert_ready_document(settings: Settings, document_id: str, filename: str) -> str:
    initialize_database(settings)
    with connect(settings) as connection:
        connection.execute(
            """
            INSERT INTO documents (
                id, original_filename, stored_filename, content_hash, file_type,
                byte_size, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'ready', datetime('now'), datetime('now'))
            """,
            (document_id, filename, f"{document_id}.txt", document_id, "txt", 10),
        )
        chunk_id = f"{document_id}:0:0-10"
        connection.execute(
            """
            INSERT INTO document_chunks (
                id, document_id, chunk_index, content, start_char, end_char, created_at
            ) VALUES (?, ?, 0, ?, 0, 10, datetime('now'))
            """,
            (chunk_id, document_id, "A remembered passage"),
        )
    return chunk_id


def test_search_resolves_sqlite_metadata_and_bounds_top_k(temp_settings: Settings) -> None:
    store = FakeVectorStore()
    chunk_id = _insert_ready_document(temp_settings, "doc-1", "journal.txt")
    store.upsert([chunk_id], [[1.0]], ["untrusted vector copy"], [{"document_id": "doc-1"}])

    results = search_documents(
        temp_settings,
        "memory",
        99,
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=store,
    )

    assert store.last_top_k == 8
    assert results[0]["text"] == "A remembered passage"
    assert results[0]["filename"] == "journal.txt"


def test_search_empty_archive_returns_empty(temp_settings: Settings) -> None:
    results = search_documents(
        temp_settings,
        "anything",
        5,
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=FakeVectorStore(),
    )

    assert results == []


def test_search_drops_orphan_vector(temp_settings: Settings) -> None:
    store = FakeVectorStore()
    store.records["missing"] = {
        "embedding": [1.0],
        "document": "private",
        "metadata": {"document_id": "missing-doc"},
    }

    assert (
        search_documents(
            temp_settings,
            "anything",
            5,
            embedding_provider=FakeEmbeddingProvider(),
            vector_store=store,
        )
        == []
    )


def test_rebuild_index_reads_ready_chunks_from_sqlite(temp_settings: Settings) -> None:
    store = FakeVectorStore()
    _insert_ready_document(temp_settings, "doc-1", "journal.txt")

    rebuilt = rebuild_index_from_sqlite(
        temp_settings,
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=store,
    )

    assert rebuilt == 1
    assert len(store.records) == 1


def test_upload_embeds_and_persists_ready_state(temp_settings: Settings) -> None:
    fake_store = FakeVectorStore()
    upload = UploadFile(filename="memory.txt", file=BytesIO(b"A local memory."))

    document, duplicate = asyncio.run(
        ingest_upload(
            temp_settings,
            upload,
            embedding_provider=FakeEmbeddingProvider(),
            vector_store=fake_store,
        )
    )

    assert duplicate is False
    assert document["status"] == "ready"
    assert fake_store.records
    assert list(Path(temp_settings.files_dir).iterdir())


def test_search_route_returns_empty_without_documents(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.search.search_documents",
        lambda *args, **kwargs: [],
    )
    response = client.post("/api/search", json={"query": "missing"})
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


def test_real_semantic_search_survives_new_store_instance(temp_settings: Settings) -> None:
    sample_path = (
        Path(__file__).parents[2] / "data" / "sample_archive" / "notes" / "botanical_notes.md"
    )
    upload = UploadFile(
        filename=sample_path.name,
        file=BytesIO(sample_path.read_bytes()),
    )
    provider = get_embedding_provider(temp_settings.embedding_model)
    store = ChromaVectorStore(temp_settings)

    document, duplicate = asyncio.run(
        ingest_upload(
            temp_settings,
            upload,
            embedding_provider=provider,
            vector_store=store,
        )
    )
    results = search_documents(
        temp_settings,
        "Who examined the purple flowering specimen?",
        5,
        embedding_provider=provider,
        vector_store=ChromaVectorStore(temp_settings),
    )

    assert duplicate is False
    assert document["status"] == "ready"
    assert results
    assert results[0]["document_id"] == document["id"]
    assert "Ashworth" in results[0]["text"]
