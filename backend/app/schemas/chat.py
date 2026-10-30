"""Grounded chat API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=2_000)
    document_ids: list[str] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=8)

    @field_validator("question")
    @classmethod
    def trim_question(cls, value: str) -> str:
        question = value.strip()
        if not question:
            raise ValueError("Question cannot be empty.")
        return question


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    document_id: str
    filename: str
    document_title: str | None = None
    page_number: int | None = None
    excerpt: str
    evidence_type: str = "direct"


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str
    direct_answer: str = ""
    archive_context: str | None = None
    limitations: list[str] = Field(default_factory=list)
    insufficient_evidence: bool
    citations: list[Citation]
    retrieval_count: int
    model: str
