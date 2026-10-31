"""Conversation service orchestration."""

from __future__ import annotations

from typing import Any

from app.core.config import Settings
from app.core.errors import ErrorCode, GhostArchiveException
from app.database.connection import connect, initialize_database
from app.database.repositories import conversations as repo


def create_conversation(
    settings: Settings,
    title: str | None = None,
) -> dict[str, Any]:
    """Create a new conversation, defaulting title if omitted."""
    initialize_database(settings)
    default_title = (title or "New Conversation").strip()
    with connect(settings) as conn:
        return repo.create_conversation(conn, default_title)


def get_conversation_detail(
    settings: Settings,
    conversation_id: str,
) -> dict[str, Any]:
    """Get full conversation detail with messages and decorated citations."""
    initialize_database(settings)
    with connect(settings) as conn:
        conv = repo.get_conversation(conn, conversation_id)
        if not conv:
            raise GhostArchiveException(
                ErrorCode.NOT_FOUND,
                f"Conversation '{conversation_id}' does not exist.",
                404,
            )
        messages = repo.list_messages(conn, conversation_id)
        return {
            **conv,
            "messages": messages,
        }


def list_conversations(
    settings: Settings,
    limit: int = 50,
    offset: int = 0,
    query: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """List conversations with message count and preview."""
    initialize_database(settings)
    with connect(settings) as conn:
        items = repo.list_conversations(conn, limit=limit, offset=offset, search_query=query)
        total = repo.count_conversations(conn, search_query=query)
        return items, total


def rename_conversation(
    settings: Settings,
    conversation_id: str,
    title: str,
) -> dict[str, Any]:
    """Rename a conversation title."""
    initialize_database(settings)
    clean_title = title.strip()
    if not clean_title:
        raise GhostArchiveException(
            ErrorCode.VALIDATION_ERROR,
            "Conversation title cannot be empty.",
            400,
        )
    with connect(settings) as conn:
        conv = repo.get_conversation(conn, conversation_id)
        if not conv:
            raise GhostArchiveException(
                ErrorCode.NOT_FOUND,
                f"Conversation '{conversation_id}' does not exist.",
                404,
            )
        updated = repo.update_conversation_title(conn, conversation_id, clean_title)
        return updated or conv


def remove_conversation(
    settings: Settings,
    conversation_id: str,
) -> bool:
    """Delete a conversation and cascade delete its messages."""
    initialize_database(settings)
    with connect(settings) as conn:
        conv = repo.get_conversation(conn, conversation_id)
        if not conv:
            raise GhostArchiveException(
                ErrorCode.NOT_FOUND,
                f"Conversation '{conversation_id}' does not exist.",
                404,
            )
        return repo.delete_conversation(conn, conversation_id)
