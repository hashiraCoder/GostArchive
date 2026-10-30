"""Semantic search route."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.search import SearchRequest, SearchResponse, SearchResult
from app.services.search_service import search_documents

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(
    request: SearchRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> SearchResponse:
    items = search_documents(
        settings,
        request.query,
        request.top_k,
        request.document_ids,
    )
    return SearchResponse(
        items=[SearchResult(**item) for item in items],
        total=len(items),
    )
