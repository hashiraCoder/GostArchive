"""SQLite repository for conversations and messages."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def create_conversation(
    connection: sqlite3.Connection,
    title: str,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    """Create a new conversation."""
    cid = conversation_id or str(uuid.uuid4())
    now = _utc_now()
    connection.execute(
        """
        INSERT INTO conversations (id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (cid, title.strip(), now, now),
    )
    return {
        "id": cid,
        "title": title.strip(),
        "created_at": now,
        "updated_at": now,
    }


def get_conversation(
    connection: sqlite3.Connection,
    conversation_id: str,
) -> dict[str, Any] | None:
    """Fetch conversation metadata by ID."""
    cursor = connection.execute(
        """
        SELECT id, title, created_at, updated_at
        FROM conversations
        WHERE id = ?
        """,
        (conversation_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return dict(row)


def list_conversations(
    connection: sqlite3.Connection,
    limit: int = 50,
    offset: int = 0,
    search_query: str | None = None,
) -> list[dict[str, Any]]:
    """List conversations ordered by updated_at descending with message counts."""
    query = """
        SELECT
            c.id,
            c.title,
            c.created_at,
            c.updated_at,
            COUNT(m.id) AS message_count,
            (
                SELECT content FROM messages
                WHERE conversation_id = c.id
                ORDER BY created_at DESC LIMIT 1
            ) AS last_message_preview
        FROM conversations c
        LEFT JOIN messages m ON m.conversation_id = c.id
    """
    params: list[Any] = []
    if search_query and search_query.strip():
        query += " WHERE c.title LIKE ?"
        params.append(f"%{search_query.strip()}%")

    query += " GROUP BY c.id ORDER BY c.updated_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor = connection.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def count_conversations(
    connection: sqlite3.Connection,
    search_query: str | None = None,
) -> int:
    """Return total count of conversations."""
    if search_query and search_query.strip():
        cursor = connection.execute(
            "SELECT COUNT(*) FROM conversations WHERE title LIKE ?",
            (f"%{search_query.strip()}%",),
        )
    else:
        cursor = connection.execute("SELECT COUNT(*) FROM conversations")
    return int(cursor.fetchone()[0])


def update_conversation_title(
    connection: sqlite3.Connection,
    conversation_id: str,
    title: str,
) -> dict[str, Any] | None:
    """Rename a conversation."""
    now = _utc_now()
    cursor = connection.execute(
        """
        UPDATE conversations
        SET title = ?, updated_at = ?
        WHERE id = ?
        RETURNING id, title, created_at, updated_at
        """,
        (title.strip(), now, conversation_id),
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def touch_conversation(connection: sqlite3.Connection, conversation_id: str) -> None:
    """Update conversation updated_at timestamp."""
    connection.execute(
        "UPDATE conversations SET updated_at = ? WHERE id = ?",
        (_utc_now(), conversation_id),
    )


def delete_conversation(connection: sqlite3.Connection, conversation_id: str) -> bool:
    """Delete a conversation, cascading to its messages."""
    cursor = connection.execute(
        "DELETE FROM conversations WHERE id = ?",
        (conversation_id,),
    )
    return cursor.rowcount > 0


def add_message(
    connection: sqlite3.Connection,
    conversation_id: str,
    role: str,
    content: str,
    *,
    status: str = "completed",
    client_turn_id: str | None = None,
    direct_answer: str | None = None,
    archive_context: str | None = None,
    limitations: list[str] | None = None,
    insufficient_evidence: bool = False,
    citations: list[dict[str, Any]] | None = None,
    retrieval_count: int = 0,
    model: str | None = None,
    error_message: str | None = None,
    scope_document_ids: list[str] | None = None,
    message_id: str | None = None,
) -> dict[str, Any]:
    """Add a message to a conversation."""
    mid = message_id or str(uuid.uuid4())
    now = _utc_now()
    citations_json = json.dumps(citations) if citations is not None else None
    limitations_json = json.dumps(limitations) if limitations is not None else None
    scope_json = json.dumps(scope_document_ids) if scope_document_ids is not None else None

    connection.execute(
        """
        INSERT INTO messages (
            id, conversation_id, client_turn_id, role, content, status,
            direct_answer, archive_context, limitations, insufficient_evidence,
            citations, retrieval_count, model, error_message, scope_document_ids,
            created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            mid,
            conversation_id,
            client_turn_id,
            role,
            content,
            status,
            direct_answer,
            archive_context,
            limitations_json,
            1 if insufficient_evidence else 0,
            citations_json,
            retrieval_count,
            model,
            error_message,
            scope_json,
            now,
            now,
        ),
    )
    return {
        "id": mid,
        "conversation_id": conversation_id,
        "client_turn_id": client_turn_id,
        "role": role,
        "content": content,
        "status": status,
        "direct_answer": direct_answer,
        "archive_context": archive_context,
        "limitations": limitations or [],
        "insufficient_evidence": insufficient_evidence,
        "citations": citations or [],
        "retrieval_count": retrieval_count,
        "model": model,
        "error_message": error_message,
        "scope_document_ids": scope_document_ids or [],
        "created_at": now,
        "updated_at": now,
    }


def get_message_by_turn(
    connection: sqlite3.Connection,
    conversation_id: str,
    client_turn_id: str,
    role: str,
) -> dict[str, Any] | None:
    """Find a message by client_turn_id and role."""
    cursor = connection.execute(
        """
        SELECT * FROM messages
        WHERE conversation_id = ? AND client_turn_id = ? AND role = ?
        """,
        (conversation_id, client_turn_id, role),
    )
    row = cursor.fetchone()
    if not row:
        return None
    d = dict(row)
    d["limitations"] = json.loads(d["limitations"]) if d.get("limitations") else []
    d["citations"] = json.loads(d["citations"]) if d.get("citations") else []
    d["scope_document_ids"] = (
        json.loads(d["scope_document_ids"]) if d.get("scope_document_ids") else []
    )
    d["insufficient_evidence"] = bool(d.get("insufficient_evidence", 0))
    return d


def update_assistant_message(
    connection: sqlite3.Connection,
    message_id: str,
    *,
    status: str,
    content: str | None = None,
    direct_answer: str | None = None,
    archive_context: str | None = None,
    limitations: list[str] | None = None,
    insufficient_evidence: bool = False,
    citations: list[dict[str, Any]] | None = None,
    retrieval_count: int = 0,
    model: str | None = None,
    error_message: str | None = None,
) -> dict[str, Any] | None:
    """Update assistant message after inference completion or failure."""
    now = _utc_now()
    citations_json = json.dumps(citations) if citations is not None else None
    limitations_json = json.dumps(limitations) if limitations is not None else None

    connection.execute(
        """
        UPDATE messages
        SET status = ?,
            content = COALESCE(?, content),
            direct_answer = ?,
            archive_context = ?,
            limitations = ?,
            insufficient_evidence = ?,
            citations = ?,
            retrieval_count = ?,
            model = COALESCE(?, model),
            error_message = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            status,
            content,
            direct_answer,
            archive_context,
            limitations_json,
            1 if insufficient_evidence else 0,
            citations_json,
            retrieval_count,
            model,
            error_message,
            now,
            message_id,
        ),
    )
    cursor = connection.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
    row = cursor.fetchone()
    if not row:
        return None
    d = dict(row)
    d["limitations"] = json.loads(d["limitations"]) if d.get("limitations") else []
    d["citations"] = json.loads(d["citations"]) if d.get("citations") else []
    d["scope_document_ids"] = (
        json.loads(d["scope_document_ids"]) if d.get("scope_document_ids") else []
    )
    d["insufficient_evidence"] = bool(d.get("insufficient_evidence", 0))
    return d


def check_pending_turn(
    connection: sqlite3.Connection,
    conversation_id: str,
    timeout_seconds: int = 60,
) -> dict[str, Any] | None:
    """
    Check if a message in this conversation is currently pending.

    If a message has been pending longer than timeout_seconds, it is treated
    as stale (e.g. process crashed) and marked failed for recovery.
    """
    cursor = connection.execute(
        """
        SELECT * FROM messages
        WHERE conversation_id = ? AND status = 'pending'
        ORDER BY created_at DESC LIMIT 1
        """,
        (conversation_id,),
    )
    row = cursor.fetchone()
    if not row:
        return None

    created_iso = row["created_at"]
    try:
        created_dt = datetime.fromisoformat(created_iso)
        age_seconds = (datetime.now(UTC) - created_dt).total_seconds()
    except Exception:
        age_seconds = 999.0

    if age_seconds > timeout_seconds:
        # Recover stale pending turn from a crashed process
        mid = row["id"]
        now = _utc_now()
        connection.execute(
            """
            UPDATE messages
            SET status = 'failed',
                error_message = 'Operation timed out or was interrupted.',
                updated_at = ?
            WHERE id = ?
            """,
            (now, mid),
        )
        return None

    d = dict(row)
    return d


def list_messages(
    connection: sqlite3.Connection,
    conversation_id: str,
) -> list[dict[str, Any]]:
    """List all messages in chronological order, decorating citations with document existence."""
    cursor = connection.execute(
        """
        SELECT * FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
        """,
        (conversation_id,),
    )
    rows = cursor.fetchall()
    messages: list[dict[str, Any]] = []

    # Collect document_ids to verify existence against documents table in one batch query
    referenced_doc_ids: set[str] = set()
    for row in rows:
        c_raw = row["citations"]
        if c_raw:
            try:
                for c in json.loads(c_raw):
                    if isinstance(c, dict) and "document_id" in c:
                        referenced_doc_ids.add(c["document_id"])
            except Exception:
                pass

    existing_doc_ids: set[str] = set()
    if referenced_doc_ids:
        placeholders = ",".join("?" for _ in referenced_doc_ids)
        doc_cursor = connection.execute(
            f"SELECT id FROM documents WHERE id IN ({placeholders})",
            list(referenced_doc_ids),
        )
        existing_doc_ids = {r[0] for r in doc_cursor.fetchall()}

    for row in rows:
        d = dict(row)
        d["limitations"] = json.loads(d["limitations"]) if d.get("limitations") else []
        raw_citations = json.loads(d["citations"]) if d.get("citations") else []
        decorated_citations = []
        for c in raw_citations:
            if isinstance(c, dict):
                c_copy = dict(c)
                c_copy["document_exists"] = c.get("document_id") in existing_doc_ids
                decorated_citations.append(c_copy)
            else:
                decorated_citations.append(c)
        d["citations"] = decorated_citations
        d["scope_document_ids"] = (
            json.loads(d["scope_document_ids"]) if d.get("scope_document_ids") else []
        )
        d["insufficient_evidence"] = bool(d.get("insufficient_evidence", 0))
        messages.append(d)

    return messages


def get_recent_completed_turns(
    connection: sqlite3.Connection,
    conversation_id: str,
    limit_turns: int = 3,
    active_scope_ids: list[str] | None = None,
    exclude_turn_id: str | None = None,
) -> list[dict[str, str]]:
    """
    Retrieve previous completed turns for bounded LLM context.

    Enforces Scope Isolation: If the active query is restricted to a document scope,
    assistant responses from broader or incompatible scopes are omitted to prevent
    claims from other documents leaking into the narrower scope.
    """
    query = """
        SELECT role, content, status, scope_document_ids, client_turn_id
        FROM messages
        WHERE conversation_id = ? AND status = 'completed'
    """
    params: list[Any] = [conversation_id]
    if exclude_turn_id:
        query += " AND (client_turn_id != ? OR client_turn_id IS NULL)"
        params.append(exclude_turn_id)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit_turns * 2)

    cursor = connection.execute(query, params)
    rows = list(cursor.fetchall())
    rows.reverse()  # Chronological order

    turns: list[dict[str, str]] = []
    active_set = set(active_scope_ids) if active_scope_ids else None

    for r in rows:
        role = r["role"]
        content = r["content"]
        raw_scope = r["scope_document_ids"]
        turn_scope: set[str] = set()
        if raw_scope:
            try:
                turn_scope = set(json.loads(raw_scope))
            except Exception:
                turn_scope = set()

        if (
            role == "assistant"
            and active_set is not None
            and (not turn_scope or not turn_scope.issubset(active_set))
        ):
            # If active scope is narrower, only include assistant turns scoped to a subset
            continue

        turns.append({"role": role, "content": content})

    return turns
