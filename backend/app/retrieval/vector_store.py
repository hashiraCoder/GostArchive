"""Persistent Chroma vector-store adapter."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.core.config import Settings

COLLECTION_NAME = "ghostarchive_chunks"


class ChromaVectorStore:
    """Chroma adapter storing chunk IDs and minimal filter metadata."""

    def __init__(self, settings: Settings, client: Any = None) -> None:
        self._settings = settings
        self._client = client

    @property
    def client(self) -> Any:
        if self._client is None:
            import chromadb

            self._settings.chroma_path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(self._settings.chroma_path))
        return self._client

    @property
    def collection(self) -> Any:
        return self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={
                "embedding_model": self._settings.embedding_model,
                "hnsw:space": "cosine",
            },
        )

    def upsert(
        self,
        ids: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        documents: Sequence[str],
        metadatas: Sequence[dict[str, Any]],
    ) -> None:
        if not ids:
            return
        self.collection.upsert(
            ids=list(ids),
            embeddings=[list(embedding) for embedding in embeddings],
            documents=list(documents),
            metadatas=list(metadatas),
        )

    def query(
        self,
        embedding: Sequence[float],
        top_k: int,
        document_ids: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        where = None
        if document_ids:
            where = {"document_id": {"$in": list(document_ids)}}
        return self.collection.query(
            query_embeddings=[list(embedding)],
            n_results=top_k,
            where=where,
            include=["distances", "metadatas"],
        )

    def delete(self, ids: Sequence[str]) -> None:
        if ids:
            self.collection.delete(ids=list(ids))

    def count(self) -> int:
        return self.collection.count()
