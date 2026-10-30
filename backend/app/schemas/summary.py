"""Archive and document summary schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SummaryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str | None = None
    max_chunks: int = Field(default=12, ge=1, le=30)


class SummaryDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    filename: str
    chunk_count: int


class SummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    scope: str
    inspected_documents: list[SummaryDocument]
    limitations: list[str] = Field(default_factory=list)
    model: str
