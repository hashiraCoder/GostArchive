"""Document API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    filename: str
    file_type: str
    byte_size: int
    status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document: DocumentResponse
    duplicate: bool = False


class DocumentListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[DocumentResponse]
    total: int = Field(ge=0)
