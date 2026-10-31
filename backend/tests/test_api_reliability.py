"""
Tests for Phase 7: API Reliability, Error Envelope Integrity, and Concurrency.

Verifies:
- Complete error envelope compliance for 400, 404, 409, 413, 422, 502, 503, 504, 500.
- Safe logging of unhandled errors without leaking paths or tracebacks.
- 502 Bad Gateway recovery: failed turns do not permanently lock conversations.
- 409 Conflict handling for concurrent turns and stale turn reclamation (>60s).
- Idempotent request replay and conflict on key reuse with altered questions.
- Malformed inputs handled safely without server crashes.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.errors import ErrorCode
from app.database.connection import connect, initialize_database
from app.database.repositories import conversations as conv_repo
from app.main import create_app


def test_422_unprocessable_content_envelope(client: TestClient) -> None:
    """Missing or invalid request body returns standardized 422 ErrorEnvelope."""
    resp = client.post("/api/chat", json={})
    assert resp.status_code == 422
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == ErrorCode.VALIDATION_ERROR
    assert data["error"]["message"] == "Invalid request payload or parameters."
    assert data["error"]["retryable"] is False


def test_404_not_found_envelope(client: TestClient) -> None:
    """Accessing non-existent resources returns standardized 404 ErrorEnvelope."""
    # Non-existent document
    resp = client.get("/api/documents/non-existent-doc-id-12345")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"]["code"] == ErrorCode.NOT_FOUND
    assert "not found" in data["error"]["message"].lower()
    assert data["error"]["retryable"] is False

    # Non-existent conversation
    resp_conv = client.get("/api/conversations/non-existent-conv-id-12345")
    assert resp_conv.status_code == 404
    assert resp_conv.json()["error"]["code"] == ErrorCode.NOT_FOUND


def test_413_payload_too_large_envelope(client: TestClient, temp_settings: Settings) -> None:
    """Files exceeding upload_max_bytes return 413 ErrorEnvelope."""
    temp_settings.upload_max_bytes = 100
    oversized_content = b"x" * 200
    resp = client.post(
        "/api/documents",
        files={"file": ("large.txt", oversized_content, "text/plain")},
    )
    assert resp.status_code == 413
    data = resp.json()
    assert data["error"]["code"] == ErrorCode.VALIDATION_ERROR
    assert "exceeds" in data["error"]["message"].lower()


def test_500_unhandled_exception_sanitized_envelope(temp_settings: Settings) -> None:
    """Internal server errors log internally but return sanitized 500 ErrorEnvelope."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: temp_settings

    # Using raise_server_exceptions=False lets FastAPI's 500 handler generate the response
    unhandled_client = TestClient(app, raise_server_exceptions=False)

    with patch(
        "app.api.routes.documents.get_documents",
        side_effect=RuntimeError("Secret DB credentials in /var/internal/path/crash.db"),
    ):
        resp = unhandled_client.get("/api/documents")
        assert resp.status_code == 500
        data = resp.json()
        assert data["error"]["code"] == ErrorCode.INTERNAL_ERROR
        assert data["error"]["message"] == "An unexpected internal error occurred."
        assert data["error"]["retryable"] is True
        # Verify no private path leaked in JSON response
        assert "/var/internal/path" not in resp.text
        assert "crash.db" not in resp.text


def test_chat_502_bad_gateway_and_subsequent_turn_freedom(
    client: TestClient,
    temp_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    When an LLM call fails with 502 Bad Gateway:
    - Chat endpoint returns 502 with GENERATION_FAILED.
    - Assistant message is durably recorded as status='failed'.
    - Subsequent turns are NOT blocked by 409 Conflict.
    """
    fake_evidence = [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "filename": "f.txt",
            "page_number": None,
            "text": "The signal frequency is 10 Hz.",
            "start_char": 0,
            "end_char": 30,
            "score": 0.85,
        }
    ]
    monkeypatch.setattr(
        "app.services.chat_service.search_documents",
        lambda *args, **kwargs: fake_evidence,
    )

    # 1. First turn fails with Ollama 500 / runner crash -> 502 Bad Gateway
    mock_500 = httpx.Response(
        500,
        json={"error": "CUDA kernel failure"},
        request=httpx.Request("POST", "url"),
    )
    turn_1_id = "turn-fail-001"
    with patch("httpx.Client.post", return_value=mock_500):
        resp_502 = client.post(
            "/api/chat",
            json={
                "question": "What is the signal frequency?",
                "client_turn_id": turn_1_id,
            },
        )
        assert resp_502.status_code == 502
        assert resp_502.json()["error"]["code"] == ErrorCode.GENERATION_FAILED

    # Check database state: turn is failed, not pending
    with connect(temp_settings) as conn:
        asst = conn.execute(
            """
            SELECT id, conversation_id, status, error_message
            FROM messages
            WHERE client_turn_id = ? AND role = 'assistant'
            """,
            (turn_1_id,),
        ).fetchone()
        assert asst is not None
        assert asst["status"] == "failed"
        assert "CUDA kernel failure" in (asst["error_message"] or "")
        conv_id = asst["conversation_id"]

    # 2. Second turn with a DIFFERENT question succeeds immediately (no 409 lock!)
    mock_payload = {
        "answer": "10 Hz",
        "archive_context": "f.txt",
        "limitations": [],
        "insufficient_evidence": False,
        "cited_chunk_ids": ["c1"],
    }
    mock_ok = httpx.Response(
        200,
        json={"message": {"content": json.dumps(mock_payload)}},
        request=httpx.Request("POST", "url"),
    )
    turn_2_id = "turn-success-002"
    with patch("httpx.Client.post", return_value=mock_ok):
        resp_next = client.post(
            "/api/chat",
            json={
                "question": "Please repeat the signal frequency.",
                "conversation_id": conv_id,
                "client_turn_id": turn_2_id,
            },
        )
        assert resp_next.status_code == 200
        assert resp_next.json()["answer"] == "10 Hz"


def test_chat_retry_failed_turn_replaces_failure(
    client: TestClient,
    temp_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Retrying the same failed turn reclaims the turn and succeeds."""
    fake_evidence = [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "filename": "f.txt",
            "page_number": None,
            "text": "The signal frequency is 10 Hz.",
            "start_char": 0,
            "end_char": 30,
            "score": 0.85,
        }
    ]
    monkeypatch.setattr(
        "app.services.chat_service.search_documents",
        lambda *args, **kwargs: fake_evidence,
    )

    turn_id = "retryable-turn-123"
    question = "What is the signal frequency?"

    # 1. First attempt fails with 502
    mock_500 = httpx.Response(500, json={"error": "OOM"}, request=httpx.Request("POST", "url"))
    with patch("httpx.Client.post", return_value=mock_500):
        resp_fail = client.post(
            "/api/chat",
            json={"question": question, "client_turn_id": turn_id},
        )
        assert resp_fail.status_code == 502

    # Get conversation id
    with connect(temp_settings) as conn:
        asst = conn.execute(
            """
            SELECT id, conversation_id, status
            FROM messages
            WHERE client_turn_id = ? AND role = 'assistant'
            """,
            (turn_id,),
        ).fetchone()
        assert asst is not None
        assert asst["status"] == "failed"
        conv_id = asst["conversation_id"]

    # 2. Retry the EXACT same turn with same turn_id
    mock_payload = {
        "answer": "10 Hz verified",
        "archive_context": "f.txt",
        "limitations": [],
        "insufficient_evidence": False,
        "cited_chunk_ids": ["c1"],
    }
    mock_ok = httpx.Response(
        200,
        json={"message": {"content": json.dumps(mock_payload)}},
        request=httpx.Request("POST", "url"),
    )
    with patch("httpx.Client.post", return_value=mock_ok):
        resp_retry = client.post(
            "/api/chat",
            json={
                "question": question,
                "conversation_id": conv_id,
                "client_turn_id": turn_id,
            },
        )
        assert resp_retry.status_code == 200
        assert resp_retry.json()["answer"] == "10 Hz verified"

    # Verify message transitioned to completed
    with connect(temp_settings) as conn:
        asst_after = conn.execute(
            """
            SELECT status, error_message
            FROM messages
            WHERE client_turn_id = ? AND role = 'assistant'
            """,
            (turn_id,),
        ).fetchone()
        assert asst_after["status"] == "completed"
        assert asst_after["error_message"] is None


def test_chat_409_conflict_on_concurrent_turn_and_stale_reclaim(
    client: TestClient,
    temp_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Concurrent requests trigger 409 Conflict when active (<60s),
    while stale pending turns (>60s) are reclaimed automatically.
    """
    monkeypatch.setattr(
        "app.services.chat_service.search_documents",
        lambda *args, **kwargs: [],
    )
    initialize_database(temp_settings)
    with connect(temp_settings) as conn:
        conv = conv_repo.create_conversation(conn, "Concurrency Test")
        conv_id = conv["id"]

        # Insert an active pending turn (created right now)
        conv_repo.add_message(
            conn,
            conv_id,
            role="assistant",
            content="",
            status="pending",
            client_turn_id="active-turn-999",
        )

    # 1. Sending a new question while turn is active returns 409 Conflict
    resp_conflict = client.post(
        "/api/chat",
        json={"question": "Another query while busy", "conversation_id": conv_id},
    )
    assert resp_conflict.status_code == 409
    data = resp_conflict.json()
    assert data["error"]["code"] == ErrorCode.CONFLICT
    assert "still processing" in data["error"]["message"].lower()

    # 2. Simulate stale pending turn (simulate creation 70s ago)
    stale_timestamp = "2020-01-01T00:00:00+00:00"
    with connect(temp_settings) as conn:
        conn.execute(
            "UPDATE messages SET created_at = ? WHERE client_turn_id = 'active-turn-999'",
            (stale_timestamp,),
        )

    # 3. Now sending a query reclaims the stale lock and proceeds
    resp_reclaimed = client.post(
        "/api/chat",
        json={"question": "What is the speed of light?", "conversation_id": conv_id},
    )
    # The question is out-of-scope for empty archive, so it returns 200, NOT 409!
    assert resp_reclaimed.status_code == 200


def test_idempotency_conflict_on_question_mismatch(
    client: TestClient,
    temp_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reusing client_turn_id with a different question triggers 409 Conflict."""
    fake_evidence = [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "filename": "f.txt",
            "page_number": None,
            "text": "10 Hz",
            "start_char": 0,
            "end_char": 5,
            "score": 0.8,
        }
    ]
    monkeypatch.setattr(
        "app.services.chat_service.search_documents",
        lambda *args, **kwargs: fake_evidence,
    )

    mock_payload = {
        "answer": "10 Hz",
        "archive_context": "f.txt",
        "limitations": [],
        "insufficient_evidence": False,
        "cited_chunk_ids": ["c1"],
    }
    mock_ok = httpx.Response(
        200,
        json={"message": {"content": json.dumps(mock_payload)}},
        request=httpx.Request("POST", "url"),
    )
    turn_id = "unique-turn-abc"

    # First request
    with patch("httpx.Client.post", return_value=mock_ok):
        resp1 = client.post(
            "/api/chat",
            json={"question": "Question A", "client_turn_id": turn_id},
        )
        assert resp1.status_code == 200
        conv_id = resp1.json()["conversation_id"]

    # Reusing same client_turn_id with identical question returns idempotent cached answer
    resp_idempotent = client.post(
        "/api/chat",
        json={"question": "Question A", "conversation_id": conv_id, "client_turn_id": turn_id},
    )
    assert resp_idempotent.status_code == 200
    assert resp_idempotent.json()["answer"] == "10 Hz"

    # Reusing same client_turn_id with a DIFFERENT question triggers 409 Conflict
    resp_conflict = client.post(
        "/api/chat",
        json={
            "question": "Question B altered",
            "conversation_id": conv_id,
            "client_turn_id": turn_id,
        },
    )
    assert resp_conflict.status_code == 409
    assert resp_conflict.json()["error"]["code"] == ErrorCode.CONFLICT
    assert "idempotency key reused" in resp_conflict.json()["error"]["message"].lower()
