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
    error_code: str | None = None


class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document: DocumentResponse
    duplicate: bool = False


class DocumentListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[DocumentResponse]
    total: int = Field(ge=0)


class BulkDeleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_ids: list[str] = Field(min_length=1)


class BulkDeleteResultItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    success: bool
    error: str | None = None


class BulkDeleteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    results: list[BulkDeleteResultItem]
    total_deleted: int = Field(ge=0)
