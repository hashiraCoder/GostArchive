"""Conversation and message API contracts."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConversationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=200)

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str | None) -> str | None:
        if v is not None:
            cleaned = v.strip()
            return cleaned if cleaned else None
        return None


class ConversationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Title cannot be empty.")
        return cleaned


class CitationSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    document_id: str
    filename: str
    document_title: str | None = None
    page_number: int | None = None
    excerpt: str
    evidence_type: str = "direct"
    document_exists: bool = True


class MessageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    conversation_id: str
    client_turn_id: str | None = None
    role: str
    content: str
    status: str
    direct_answer: str | None = None
    archive_context: str | None = None
    limitations: list[str] = Field(default_factory=list)
    insufficient_evidence: bool = False
    citations: list[CitationSnapshot] = Field(default_factory=list)
    retrieval_count: int = 0
    model: str | None = None
    error_message: str | None = None
    scope_document_ids: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class ConversationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0
    last_message_preview: str | None = None


class ConversationListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ConversationSummary]
    total: int


class ConversationDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[MessageResponse]
