"""Test suite for Conversation Persistence, multi-turn context, and failure recovery."""

from unittest.mock import patch

import httpx
from starlette.testclient import TestClient


def test_auto_creation_and_backward_compatibility(client: TestClient) -> None:
    """Calling /api/chat without conversation_id auto-creates a conversation."""
    fake_evidence = [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "filename": "notes.txt",
            "page_number": None,
            "text": "The secret code is 4242.",
            "start_char": 0,
            "end_char": 24,
            "score": 0.95,
        }
    ]
    mock_model_output = (
        '{"answer": "The secret code is 4242.", "insufficient_evidence": false, '
        '"cited_chunk_ids": ["c1"]}'
    )

    with (
        patch("app.services.chat_service.search_documents", lambda *args, **kwargs: fake_evidence),
        patch("app.generation.ollama_client.OllamaClient.chat", return_value=mock_model_output),
    ):
        res = client.post("/api/chat", json={"question": "What is the secret code?"})
        assert res.status_code == 200
        data = res.json()
        assert data["answer"] == "The secret code is 4242."
        assert data["conversation_id"] is not None
        assert data["message_id"] is not None
        conv_id = data["conversation_id"]

        # Verify conversation was persisted
        conv_res = client.get(f"/api/conversations/{conv_id}")
        assert conv_res.status_code == 200
        conv_data = conv_res.json()
        assert len(conv_data["messages"]) == 2
        assert conv_data["messages"][0]["role"] == "user"
        assert conv_data["messages"][0]["content"] == "What is the secret code?"
        assert conv_data["messages"][1]["role"] == "assistant"
        assert conv_data["messages"][1]["content"] == "The secret code is 4242."
        assert conv_data["messages"][1]["status"] == "completed"


def test_multiturn_context_passed_to_llm(client: TestClient) -> None:
    """Subsequent questions in a conversation pass bounded previous turns to generation prompt."""
    # 1. Create conversation
    create_res = client.post("/api/conversations", json={"title": "Lantern Tech Discussion"})
    assert create_res.status_code == 201
    cid = create_res.json()["id"]

    fake_evidence = [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "filename": "meeting.txt",
            "page_number": None,
            "text": "Project: Lantern. Stack: React, FastAPI, PostgreSQL.",
            "start_char": 0,
            "end_char": 50,
            "score": 0.9,
        }
    ]

    captured_prompts = []

    def mock_chat(self, sys_prompt, user_prompt):
        captured_prompts.append(user_prompt)
        return (
            '{"answer": "React and FastAPI.", "insufficient_evidence": false, '
            '"cited_chunk_ids": ["c1"]}'
        )

    with (
        patch("app.services.chat_service.search_documents", lambda *args, **kwargs: fake_evidence),
        patch("app.generation.ollama_client.OllamaClient.chat", mock_chat),
    ):
        # Turn 1
        t1 = client.post(
            "/api/chat",
            json={
                "conversation_id": cid,
                "question": "What technologies did I use for Lantern?",
                "client_turn_id": "turn-1",
            },
        )
        assert t1.status_code == 200

        # Turn 2: Follow-up question
        t2 = client.post(
            "/api/chat",
            json={
                "conversation_id": cid,
                "question": "Why did we reject Redis?",
                "client_turn_id": "turn-2",
            },
        )
        assert t2.status_code == 200

        # Turn 2 user_prompt MUST contain bounded conversation history for reference
        assert len(captured_prompts) == 2
        turn2_prompt = captured_prompts[1]
        assert "Previous Conversation Turns" in turn2_prompt
        assert "What technologies did I use for Lantern?" in turn2_prompt
        assert "React and FastAPI." in turn2_prompt
        assert "Current Question:\nWhy did we reject Redis?" in turn2_prompt


def test_failure_handling_and_idempotent_retry(client: TestClient) -> None:
    """When inference fails, message is saved as failed and retry does not duplicate."""
    create_res = client.post("/api/conversations", json={"title": "Retry Test"})
    cid = create_res.json()["id"]

    fake_evidence = [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "filename": "f.txt",
            "page_number": None,
            "text": "evidence",
            "start_char": 0,
            "end_char": 8,
            "score": 0.9,
        }
    ]

    # 1. Simulate failure during first attempt
    with (
        patch("app.services.chat_service.search_documents", lambda *args, **kwargs: fake_evidence),
        patch("httpx.Client.post", side_effect=httpx.ConnectError("Ollama connection refused")),
    ):
        fail_res = client.post(
            "/api/chat",
            json={
                "conversation_id": cid,
                "question": "When was mobilization?",
                "client_turn_id": "turn-fail-1",
            },
        )
        assert fail_res.status_code == 503
        assert fail_res.json()["error"]["code"] == "MODEL_UNAVAILABLE"

    # Verify conversation state: exactly 1 user message (completed) and 1 assistant message (failed)
    thread = client.get(f"/api/conversations/{cid}").json()
    assert len(thread["messages"]) == 2
    assert thread["messages"][0]["role"] == "user"
    assert thread["messages"][0]["status"] == "completed"
    assert thread["messages"][1]["role"] == "assistant"
    assert thread["messages"][1]["status"] == "failed"
    assert "unreachable" in thread["messages"][1]["error_message"].lower()

    # 2. Retry with the SAME client_turn_id, this time with working model
    mock_success = (
        '{"answer": "August 1914.", "insufficient_evidence": false, "cited_chunk_ids": ["c1"]}'
    )
    with (
        patch("app.services.chat_service.search_documents", lambda *args, **kwargs: fake_evidence),
        patch("app.generation.ollama_client.OllamaClient.chat", return_value=mock_success),
    ):
        retry_res = client.post(
            "/api/chat",
            json={
                "conversation_id": cid,
                "question": "When was mobilization?",
                "client_turn_id": "turn-fail-1",
            },
        )
        assert retry_res.status_code == 200
        assert retry_res.json()["answer"] == "August 1914."

    # Verify thread STILL has exactly 2 messages (no duplicates!), assistant updated to completed
    thread_after = client.get(f"/api/conversations/{cid}").json()
    assert len(thread_after["messages"]) == 2
    assert thread_after["messages"][0]["content"] == "When was mobilization?"
    assert thread_after["messages"][1]["status"] == "completed"
    assert thread_after["messages"][1]["content"] == "August 1914."


def test_idempotency_conflict_on_different_question(client: TestClient) -> None:
    """Reusing client_turn_id with a different question raises HTTP 409 Conflict."""
    create_res = client.post("/api/conversations", json={"title": "Idempotency Test"})
    cid = create_res.json()["id"]

    fake_evidence = [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "filename": "f.txt",
            "page_number": None,
            "text": "t",
            "start_char": 0,
            "end_char": 1,
            "score": 0.9,
        }
    ]
    mock_out = '{"answer": "ans", "insufficient_evidence": false, "cited_chunk_ids": ["c1"]}'

    with (
        patch("app.services.chat_service.search_documents", lambda *args, **kwargs: fake_evidence),
        patch("app.generation.ollama_client.OllamaClient.chat", return_value=mock_out),
    ):
        res1 = client.post(
            "/api/chat",
            json={
                "conversation_id": cid,
                "question": "Original question?",
                "client_turn_id": "turn-reuse-1",
            },
        )
        assert res1.status_code == 200

        # Now reuse the same turn ID with a different question
        res2 = client.post(
            "/api/chat",
            json={
                "conversation_id": cid,
                "question": "Completely different question?",
                "client_turn_id": "turn-reuse-1",
            },
        )
        assert res2.status_code == 409
        assert "Idempotency key reused" in res2.json()["error"]["message"]


def test_citation_snapshot_survival_after_document_deletion(client: TestClient) -> None:
    """Historical citations remain renderable and show document_exists=False when deleted."""
    # 1. Ingest document
    upload = client.post(
        "/api/documents",
        files={
            "file": (
                "historical_charter.txt",
                b"Charter granted in 1782 by the Council.",
                "text/plain",
            )
        },
    )
    assert upload.status_code == 201
    doc_id = upload.json()["document"]["id"]

    # 2. Ask question and persist in conversation
    mock_out = (
        '{"answer": "Charter was granted in 1782.", "insufficient_evidence": false, '
        f'"cited_chunk_ids": ["{doc_id}:0:0-39"]}}'
    )
    with patch("app.generation.ollama_client.OllamaClient.chat", return_value=mock_out):
        chat_res = client.post(
            "/api/chat",
            json={
                "question": "When was the charter granted?",
                "document_ids": [doc_id],
            },
        )
        assert chat_res.status_code == 200
        cid = chat_res.json()["conversation_id"]

    # Before document deletion: citation snapshot has document_exists=True
    conv_before = client.get(f"/api/conversations/{cid}").json()
    assert conv_before["messages"][1]["citations"][0]["document_exists"] is True

    # 3. Delete original document from archive
    del_res = client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == 204

    # 4. Fetch conversation history again: citation excerpt remains intact, document_exists=False
    conv_after = client.get(f"/api/conversations/{cid}").json()
    citation = conv_after["messages"][1]["citations"][0]
    assert citation["filename"] == "historical_charter.txt"
    assert citation["excerpt"] == "Charter granted in 1782 by the Council."
    assert citation["document_exists"] is False  # Correctly labeled


def test_empty_conversation_lifecycle(client: TestClient) -> None:
    """Can create, list, rename, and delete an empty conversation."""
    # Create
    c_res = client.post("/api/conversations", json={"title": "Empty Thread"})
    assert c_res.status_code == 201
    cid = c_res.json()["id"]

    # List
    list_res = client.get("/api/conversations")
    assert list_res.status_code == 200
    ids = [item["id"] for item in list_res.json()["items"]]
    assert cid in ids

    # Rename
    patch_res = client.patch(f"/api/conversations/{cid}", json={"title": "Updated Title"})
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Updated Title"

    # Delete
    del_res = client.delete(f"/api/conversations/{cid}")
    assert del_res.status_code == 204

    # Verify 404
    get_res = client.get(f"/api/conversations/{cid}")
    assert get_res.status_code == 404


def test_scoped_multiturn_context_passed_to_llm(client: TestClient) -> None:
    """When a chat is scoped to a document, previous assistant turns in that scope are retained."""
    create_res = client.post("/api/conversations", json={"title": "Scoped Multi-Turn"})
    assert create_res.status_code == 201
    cid = create_res.json()["id"]

    fake_evidence = [
        {
            "chunk_id": "doc1:0:0-30",
            "document_id": "doc1",
            "filename": "signals.txt",
            "page_number": None,
            "text": "The sampling frequency fs is 20 Hz.",
            "start_char": 0,
            "end_char": 35,
            "score": 0.95,
        }
    ]

    captured_prompts = []

    def mock_chat(self, sys_prompt, user_prompt):
        captured_prompts.append(user_prompt)
        return (
            '{"answer": "The sampling frequency is 20 Hz.", "insufficient_evidence": false, '
            '"cited_chunk_ids": ["doc1:0:0-30"]}'
        )

    with (
        patch("app.services.chat_service.search_documents", lambda *args, **kwargs: fake_evidence),
        patch("app.generation.ollama_client.OllamaClient.chat", mock_chat),
    ):
        # Turn 1 in scope doc1
        t1 = client.post(
            "/api/chat",
            json={
                "conversation_id": cid,
                "question": "What is the sampling frequency?",
                "document_ids": ["doc1"],
                "client_turn_id": "scope-turn-1",
            },
        )
        assert t1.status_code == 200

        # Turn 2 in SAME scope doc1 (BUG-12 verification)
        t2 = client.post(
            "/api/chat",
            json={
                "conversation_id": cid,
                "question": "Is it sufficient?",
                "document_ids": ["doc1"],
                "client_turn_id": "scope-turn-2",
            },
        )
        assert t2.status_code == 200

        # Turn 2 MUST have Turn 1 assistant answer in context
        assert len(captured_prompts) == 2
        turn2_prompt = captured_prompts[1]
        assert "The sampling frequency is 20 Hz." in turn2_prompt
        assert "What is the sampling frequency?" in turn2_prompt


def test_cross_scope_context_isolation_in_chat(client: TestClient) -> None:
    """When switching scope, assistant turns from out-of-scope docs are excluded."""
    create_res = client.post("/api/conversations", json={"title": "Cross Scope Test"})
    cid = create_res.json()["id"]

    evidence_doc_a = [
        {
            "chunk_id": "docA:0:0-20",
            "document_id": "docA",
            "filename": "alpha.txt",
            "page_number": None,
            "text": "Secret Alpha is TopSecret.",
            "start_char": 0,
            "end_char": 25,
            "score": 0.95,
        }
    ]
    evidence_doc_b = [
        {
            "chunk_id": "docB:0:0-20",
            "document_id": "docB",
            "filename": "beta.txt",
            "page_number": None,
            "text": "Beta status is Operational.",
            "start_char": 0,
            "end_char": 25,
            "score": 0.95,
        }
    ]

    captured_prompts = []

    def mock_chat(self, sys_prompt, user_prompt):
        captured_prompts.append(user_prompt)
        return (
            '{"answer": "Answer recorded.", "insufficient_evidence": false, "cited_chunk_ids": []}'
        )

    # Turn 1: scoped to docA
    with (
        patch("app.services.chat_service.search_documents", lambda *args, **kwargs: evidence_doc_a),
        patch("app.generation.ollama_client.OllamaClient.chat", mock_chat),
    ):
        t1 = client.post(
            "/api/chat",
            json={
                "conversation_id": cid,
                "question": "What is the secret in Alpha?",
                "document_ids": ["docA"],
                "client_turn_id": "scope-a-1",
            },
        )
        assert t1.status_code == 200

    # Turn 2: scoped to docB
    with (
        patch("app.services.chat_service.search_documents", lambda *args, **kwargs: evidence_doc_b),
        patch("app.generation.ollama_client.OllamaClient.chat", mock_chat),
    ):
        t2 = client.post(
            "/api/chat",
            json={
                "conversation_id": cid,
                "question": "What is Beta status?",
                "document_ids": ["docB"],
                "client_turn_id": "scope-b-1",
            },
        )
        assert t2.status_code == 200

        # Turn 2 prompt must NOT contain Assistant assertions from Alpha
        turn2_prompt = captured_prompts[1]
        assert "TopSecret" not in turn2_prompt


def test_bounded_context_window_caps_at_3_turns(client: TestClient) -> None:
    """Context history strictly limits to the most recent 3 completed turns (6 messages)."""
    create_res = client.post("/api/conversations", json={"title": "Context Bounding"})
    cid = create_res.json()["id"]

    fake_evidence = [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "filename": "f.txt",
            "page_number": None,
            "text": "Document context",
            "start_char": 0,
            "end_char": 16,
            "score": 0.9,
        }
    ]

    captured_prompts = []

    def mock_chat(self, sys_prompt, user_prompt):
        captured_prompts.append(user_prompt)
        turn_num = len(captured_prompts)
        return (
            f'{{"answer": "Answer {turn_num}.", "insufficient_evidence": false, '
            f'"cited_chunk_ids": ["c1"]}}'
        )

    with (
        patch("app.services.chat_service.search_documents", lambda *args, **kwargs: fake_evidence),
        patch("app.generation.ollama_client.OllamaClient.chat", mock_chat),
    ):
        # Execute 5 consecutive turns
        for i in range(1, 6):
            res = client.post(
                "/api/chat",
                json={
                    "conversation_id": cid,
                    "question": f"Question {i}?",
                    "client_turn_id": f"bounded-turn-{i}",
                },
            )
            assert res.status_code == 200

    # Turn 5 prompt should only have turns 2, 3, 4 (the last 3 completed turns)
    turn5_prompt = captured_prompts[4]
    assert "Question 1?" not in turn5_prompt
    assert "Answer 1." not in turn5_prompt
    assert "Question 2?" in turn5_prompt
    assert "Answer 2." in turn5_prompt
    assert "Question 3?" in turn5_prompt
    assert "Answer 3." in turn5_prompt
    assert "Question 4?" in turn5_prompt
    assert "Answer 4." in turn5_prompt


def test_cascade_delete_removes_messages_cleanly(client: TestClient) -> None:
    """Deleting a conversation cascades and completely removes all messages from SQLite."""
    create_res = client.post("/api/conversations", json={"title": "Cascade Delete Test"})
    cid = create_res.json()["id"]

    fake_evidence = [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "filename": "f.txt",
            "page_number": None,
            "text": "data",
            "start_char": 0,
            "end_char": 4,
            "score": 0.9,
        }
    ]
    mock_out = (
        '{"answer": "Cascade answer", "insufficient_evidence": false, "cited_chunk_ids": ["c1"]}'
    )

    with (
        patch("app.services.chat_service.search_documents", lambda *args, **kwargs: fake_evidence),
        patch("app.generation.ollama_client.OllamaClient.chat", return_value=mock_out),
    ):
        client.post(
            "/api/chat",
            json={"conversation_id": cid, "question": "Message 1?", "client_turn_id": "casc-1"},
        )
        client.post(
            "/api/chat",
            json={"conversation_id": cid, "question": "Message 2?", "client_turn_id": "casc-2"},
        )

    # Verify 4 messages in DB
    detail = client.get(f"/api/conversations/{cid}").json()
    assert len(detail["messages"]) == 4

    # Delete conversation
    del_res = client.delete(f"/api/conversations/{cid}")
    assert del_res.status_code == 204

    # Verify 404
    assert client.get(f"/api/conversations/{cid}").status_code == 404
