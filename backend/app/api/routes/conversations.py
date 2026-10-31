"""Conversation management routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.config import Settings, get_settings
from app.schemas.conversations import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationSummary,
    ConversationUpdate,
)
from app.services import conversation_service

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=ConversationListResponse)
def list_conversations(
    settings: Annotated[Settings, Depends(get_settings)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    query: Annotated[str | None, Query()] = None,
) -> ConversationListResponse:
    """List conversations ordered by most recent update."""
    items, total = conversation_service.list_conversations(
        settings, limit=limit, offset=offset, query=query
    )
    return ConversationListResponse(
        items=[ConversationSummary(**item) for item in items],
        total=total,
    )


@router.post("", response_model=ConversationSummary, status_code=status.HTTP_201_CREATED)
def create_conversation(
    request: ConversationCreate,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ConversationSummary:
    """Explicitly create a new conversation thread."""
    conv = conversation_service.create_conversation(settings, title=request.title)
    return ConversationSummary(
        id=conv["id"],
        title=conv["title"],
        created_at=conv["created_at"],
        updated_at=conv["updated_at"],
        message_count=0,
        last_message_preview=None,
    )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ConversationDetailResponse:
    """Retrieve full conversation thread and messages with citation snapshot states."""
    detail = conversation_service.get_conversation_detail(settings, conversation_id)
    return ConversationDetailResponse(**detail)


@router.patch("/{conversation_id}", response_model=ConversationSummary)
def rename_conversation(
    conversation_id: str,
    request: ConversationUpdate,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ConversationSummary:
    """Rename a conversation."""
    updated = conversation_service.rename_conversation(settings, conversation_id, request.title)
    return ConversationSummary(
        id=updated["id"],
        title=updated["title"],
        created_at=updated["created_at"],
        updated_at=updated["updated_at"],
        message_count=0,
        last_message_preview=None,
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Delete conversation and cascade delete all associated messages."""
    conversation_service.remove_conversation(settings, conversation_id)
