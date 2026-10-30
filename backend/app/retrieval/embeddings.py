"""Local Sentence Transformers embedding provider."""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from app.core.config import Settings
from app.core.errors import ErrorCode, GhostArchiveException


class EmbeddingProvider(Protocol):
    """Interface used by ingestion and search services."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed document chunks."""

    def embed_query(self, text: str) -> list[float]:
        """Embed one query."""


class SentenceTransformerProvider:
    """Lazy local embedding provider backed by Sentence Transformers."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self._settings.embedding_model)
            except Exception as exc:
                raise GhostArchiveException(
                    ErrorCode.EMBEDDING_UNAVAILABLE,
                    "The local embedding model is unavailable.",
                    503,
                    retryable=True,
                ) from exc
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings = self._get_model().encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


@lru_cache(maxsize=8)
def get_embedding_provider(model_name: str) -> SentenceTransformerProvider:
    """Return one lazy provider per configured model identifier."""
    return SentenceTransformerProvider(Settings(embedding_model=model_name))
