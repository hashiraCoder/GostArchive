"""Semantic search API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=2_000)
    document_ids: list[str] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=8)

    @field_validator("query")
    @classmethod
    def trim_query(cls, value: str) -> str:
        query = value.strip()
        if not query:
            raise ValueError("Query cannot be empty.")
        return query


class SearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    document_id: str
    filename: str
    page_number: int | None
    text: str
    start_char: int
    end_char: int
    score: float
    cosine_similarity: float = 0.0
    relevance_label: str = "Relevant"


class SearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[SearchResult]
    total: int
