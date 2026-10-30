"""Summary API route."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.summary import SummaryRequest, SummaryResponse
from app.services.summary_service import summarize_archive

router = APIRouter(prefix="/summarize", tags=["summary"])


@router.post("", response_model=SummaryResponse)
def summarize(
    request: SummaryRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> SummaryResponse:
    return SummaryResponse(
        **summarize_archive(
            settings,
            document_id=request.document_id,
            max_chunks=request.max_chunks,
        )
    )
