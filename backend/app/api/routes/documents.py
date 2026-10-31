"""Document upload and metadata routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from app.core.config import Settings, get_settings
from app.core.errors import ErrorCode, GhostArchiveException
from app.schemas.documents import (
    BulkDeleteRequest,
    BulkDeleteResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from app.services.document_service import (
    bulk_remove_documents,
    get_document_by_id,
    get_documents,
    ingest_upload,
    remove_document,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentUploadResponse:
    document, duplicate = await ingest_upload(settings, file)
    return DocumentUploadResponse(document=document, duplicate=duplicate)


@router.get("", response_model=DocumentListResponse)
def list_uploaded_documents(
    settings: Annotated[Settings, Depends(get_settings)],
    query: Annotated[str | None, Query(max_length=200)] = None,
    status: Annotated[str | None, Query(max_length=50)] = None,
    file_type: Annotated[str | None, Query(max_length=20)] = None,
    limit: Annotated[int | None, Query(ge=1, le=100)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DocumentListResponse:
    items, total = get_documents(
        settings,
        query=query,
        status=status,
        file_type=file_type,
        limit=limit,
        offset=offset,
    )
    return DocumentListResponse(items=items, total=total)


@router.post("/bulk-delete", response_model=BulkDeleteResponse)
def bulk_delete_documents(
    request: BulkDeleteRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> BulkDeleteResponse:
    results, total_deleted = bulk_remove_documents(settings, request.document_ids)
    return BulkDeleteResponse(results=results, total_deleted=total_deleted)


@router.get("/{document_id}", response_model=DocumentResponse)
def read_document(
    document_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentResponse:
    document = get_document_by_id(settings, document_id)
    if document is None:
        raise GhostArchiveException(ErrorCode.NOT_FOUND, "Document not found.", 404)
    return DocumentResponse(**document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_uploaded_document(
    document_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    remove_document(settings, document_id)
