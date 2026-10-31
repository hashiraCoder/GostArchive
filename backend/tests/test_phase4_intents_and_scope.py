"""Phase 4 verification: Query Understanding, Intent Routing, and Scope Isolation."""

from __future__ import annotations

from unittest.mock import patch

from starlette.testclient import TestClient

from app.core.config import Settings
from app.database.connection import connect, initialize_database
from app.database.repositories import conversations as conv_repo
from app.database.repositories import documents as doc_repo
from app.generation.provider import LLMProvider
from app.services.chat_service import ask_question


class DummyProvider(LLMProvider):
    """Stub LLM provider for testing."""

    model_name = "test-stub"

    def __init__(
        self,
        response: str = '{"answer": "ok", "insufficient_evidence": false, "cited_chunk_ids": []}',
    ) -> None:
        self.response = response
        self.last_system_prompt: str | None = None
        self.last_user_prompt: str | None = None
        self.call_count = 0

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        self.call_count += 1
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        return self.response


def _insert_test_doc(
    settings: Settings,
    doc_id: str,
    filename: str,
    content: str,
    chunks_text: list[str],
) -> None:
    initialize_database(settings)
    with connect(settings) as conn:
        doc = {
            "id": doc_id,
            "original_filename": filename,
            "stored_filename": f"{doc_id}.txt",
            "content_hash": f"hash-{doc_id}",
            "file_type": "txt",
            "byte_size": len(content.encode("utf-8")),
            "status": "ready",
            "title": filename,
            "source_date": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "error_code": None,
        }
        chunks = []
        offset = 0
        for i, text in enumerate(chunks_text):
            chunks.append(
                {
                    "id": f"chunk-{doc_id}-{i}",
                    "document_id": doc_id,
                    "chunk_index": i,
                    "content": text,
                    "page_number": 1,
                    "start_char": offset,
                    "end_char": offset + len(text),
                    "created_at": "2026-01-01T00:00:00Z",
                }
            )
            offset += len(text) + 2
        doc_repo.insert_document(conn, doc, chunks)

        # Write actual file to storage
        settings.files_dir.mkdir(parents=True, exist_ok=True)
        storage_file = settings.files_dir / f"{doc_id}.txt"
        storage_file.write_text(content, encoding="utf-8")


def test_full_document_retrieval_with_scope(temp_settings: Settings) -> None:
    """When scoped to a document, requesting full delivery returns verbatim text without LLM."""
    raw_content = (
        "AIM: To verify the sampling theorem.\nTheory: fs >= 2fm.\nclc;\nclear;\nclose all;\n"
    )
    chunks = [
        "AIM: To verify the sampling theorem.\nTheory: fs >= 2fm.",
        "clc;\nclear;\nclose all;",
    ]
    _insert_test_doc(temp_settings, "doc-samp", "sampling_theorem.txt", raw_content, chunks)

    provider = DummyProvider()
    res = ask_question(
        temp_settings,
        question="Deliver the whole file content to me",
        top_k=5,
        document_ids=["doc-samp"],
        persist=False,
        llm_provider=provider,
    )

    # 1. LLM was NOT called — pure zero-hallucination verbatim delivery
    assert provider.call_count == 0

    # 2. Complete verbatim content delivered
    assert res["answer"] == raw_content
    assert res["direct_answer"] == raw_content
    assert res["insufficient_evidence"] is False

    # 3. Both chunks cited with full source metadata
    assert len(res["citations"]) == 2
    assert res["citations"][0]["chunk_id"] == "chunk-doc-samp-0"
    assert res["citations"][1]["chunk_id"] == "chunk-doc-samp-1"
    assert res["citations"][0]["filename"] == "sampling_theorem.txt"


def test_full_document_retrieval_by_filename_mention(temp_settings: Settings) -> None:
    """When question mentions a document filename without scope, deliver that document verbatim."""
    _insert_test_doc(
        temp_settings,
        "doc-a",
        "report_alpha.txt",
        "Report Alpha content.",
        ["Report Alpha content."],
    )
    _insert_test_doc(
        temp_settings,
        "doc-b",
        "report_beta.txt",
        "Report Beta content.",
        ["Report Beta content."],
    )

    provider = DummyProvider()
    res = ask_question(
        temp_settings,
        question="Give me the complete file content of report_alpha.txt",
        top_k=5,
        document_ids=None,
        persist=False,
        llm_provider=provider,
    )

    assert provider.call_count == 0
    assert res["answer"] == "Report Alpha content."
    assert len(res["citations"]) == 1
    assert res["citations"][0]["filename"] == "report_alpha.txt"


def test_full_document_retrieval_multiple_docs_ambiguity(temp_settings: Settings) -> None:
    """When archive has multiple docs and none is specified in prompt, prompt user to select."""
    _insert_test_doc(temp_settings, "doc-1", "file1.txt", "1", ["1"])
    _insert_test_doc(temp_settings, "doc-2", "file2.txt", "2", ["2"])

    provider = DummyProvider()
    res = ask_question(
        temp_settings,
        question="Deliver the whole file content to me",
        top_k=5,
        document_ids=None,
        persist=False,
        llm_provider=provider,
    )

    assert provider.call_count == 0
    assert "Your archive contains multiple documents" in res["answer"]
    assert "'file1.txt'" in res["answer"]
    assert "'file2.txt'" in res["answer"]


def test_conversation_history_intent_empty(temp_settings: Settings) -> None:
    """When asking about history on a fresh conversation, return truthful notice."""
    provider = DummyProvider()
    res = ask_question(
        temp_settings,
        question="What did we just discuss?",
        top_k=5,
        persist=False,
        llm_provider=provider,
    )
    assert provider.call_count == 0
    assert "no previous messages" in res["answer"].lower()


def test_conversation_history_intent_with_turns(temp_settings: Settings) -> None:
    """When asking about history with completed turns, answer from conversation turns."""
    initialize_database(temp_settings)
    with connect(temp_settings) as conn:
        conv = conv_repo.create_conversation(conn, "Discussion Thread")
        cid = conv["id"]
        conv_repo.add_message(
            conn, cid, role="user", content="What is the Nyquist rate?", status="completed"
        )
        conv_repo.add_message(
            conn,
            cid,
            role="assistant",
            content="The Nyquist rate is fs >= 2fm.",
            status="completed",
        )

    # Question asking for previous question
    provider = DummyProvider()
    res = ask_question(
        temp_settings,
        question="What was my previous question?",
        top_k=5,
        conversation_id=cid,
        persist=False,
        llm_provider=provider,
    )
    assert provider.call_count == 0
    assert 'Your previous question was: "What is the Nyquist rate?"' in res["answer"]

    # Question asking for previous answer
    res2 = ask_question(
        temp_settings,
        question="What was your last answer?",
        top_k=5,
        conversation_id=cid,
        persist=False,
        llm_provider=provider,
    )
    assert provider.call_count == 0
    assert "The Nyquist rate is fs >= 2fm." in res2["answer"]


def test_code_explanation_intent_directive(temp_settings: Settings) -> None:
    """Code explanation queries inject special directive into LLM user prompt."""
    _insert_test_doc(
        temp_settings,
        "doc-code",
        "script.m",
        "clc; clear; close all; stem(t, x);",
        ["clc; clear; close all; stem(t, x);"],
    )

    provider = DummyProvider(
        '{"answer": "Code explained.", "insufficient_evidence": false, '
        '"cited_chunk_ids": ["chunk-doc-code-0"]}'
    )
    with patch(
        "app.services.chat_service.search_documents",
        return_value=[
            {
                "chunk_id": "chunk-doc-code-0",
                "document_id": "doc-code",
                "filename": "script.m",
                "text": "clc; clear; close all; stem(t, x);",
                "start_char": 0,
                "end_char": 34,
                "score": 0.9,
            }
        ],
    ):
        ask_question(
            temp_settings,
            question="Explain the MATLAB script",
            top_k=5,
            persist=False,
            llm_provider=provider,
        )

    assert provider.call_count == 1
    assert "Special Directive: The user asks for code explanation." in provider.last_user_prompt
    assert "Explain the exact syntax, variables, algorithms, and logic" in provider.last_user_prompt


def test_mathematical_calculation_intent_directive(temp_settings: Settings) -> None:
    """Mathematical calculation queries inject math directive into LLM user prompt."""
    provider = DummyProvider(
        '{"answer": "Nyquist rate is 1000 Hz.", "insufficient_evidence": false, '
        '"cited_chunk_ids": ["c1"]}'
    )
    with patch(
        "app.services.chat_service.search_documents",
        return_value=[
            {
                "chunk_id": "c1",
                "document_id": "d1",
                "filename": "theory.txt",
                "text": "fs >= 2fm where fm = 500 Hz.",
                "start_char": 0,
                "end_char": 29,
                "score": 0.9,
            }
        ],
    ):
        ask_question(
            temp_settings,
            question="Calculate the Nyquist rate for 500 Hz",
            top_k=5,
            persist=False,
            llm_provider=provider,
        )

    assert provider.call_count == 1
    assert (
        "Special Directive: The user asks for mathematical calculation."
        in provider.last_user_prompt
    )
    assert "Ground your answer strictly in the equations" in provider.last_user_prompt


def test_bug_04_validation_failure_marks_message_failed_without_409(client: TestClient) -> None:
    """BUG-04 fix: Invalid JSON marks assistant turn failed, avoiding 409 lock."""
    create_res = client.post("/api/conversations", json={"title": "BUG-04 Test"})
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

    # Model returns invalid non-JSON output (e.g. raw text instead of JSON schema)
    with (
        patch("app.services.chat_service.search_documents", lambda *args, **kwargs: fake_evidence),
        patch("app.generation.ollama_client.OllamaClient.chat", return_value="I am not JSON"),
    ):
        res1 = client.post(
            "/api/chat",
            json={
                "conversation_id": cid,
                "question": "What is the sampling theorem?",
                "client_turn_id": "turn-bug4-1",
            },
        )
        assert res1.status_code == 502

    # Verify assistant message in DB is marked 'failed', not stuck in 'pending'
    thread = client.get(f"/api/conversations/{cid}").json()
    assert len(thread["messages"]) == 2
    assert thread["messages"][1]["status"] == "failed"

    # Immediately submit the next question: MUST NOT be blocked with 409 Conflict!
    with (
        patch("app.services.chat_service.search_documents", lambda *args, **kwargs: fake_evidence),
        patch(
            "app.generation.ollama_client.OllamaClient.chat",
            return_value=(
                '{"answer": "Sampling theorem answered.", '
                '"insufficient_evidence": false, "cited_chunk_ids": ["c1"]}'
            ),
        ),
    ):
        res2 = client.post(
            "/api/chat",
            json={
                "conversation_id": cid,
                "question": "Second question?",
                "client_turn_id": "turn-bug4-2",
            },
        )
        # Must succeed with 200, NOT 409 Conflict!
        assert res2.status_code == 200
        assert res2.json()["answer"] == "Sampling theorem answered."


def test_cross_document_synthesis_intent_directive(temp_settings: Settings) -> None:
    """Cross-document synthesis queries inject comparison directive into prompt."""
    provider = DummyProvider(
        '{"answer": "Comparison complete.", "insufficient_evidence": false, '
        '"cited_chunk_ids": ["c1", "c2"]}'
    )
    with patch(
        "app.services.chat_service.search_documents",
        return_value=[
            {
                "chunk_id": "c1",
                "document_id": "d1",
                "filename": "docA.txt",
                "text": "Alpha specs",
                "start_char": 0,
                "end_char": 11,
                "score": 0.85,
            },
            {
                "chunk_id": "c2",
                "document_id": "d2",
                "filename": "docB.txt",
                "text": "Beta specs",
                "start_char": 0,
                "end_char": 10,
                "score": 0.80,
            },
        ],
    ):
        ask_question(
            temp_settings,
            question="Compare the documents and note the differences between A and B",
            top_k=5,
            persist=False,
            llm_provider=provider,
        )

    assert provider.call_count == 1
    assert (
        "Special Directive: The user asks for cross-document synthesis or comparison."
        in provider.last_user_prompt
    )
    assert "Compare and contrast the evidence across sources" in provider.last_user_prompt


def test_full_document_retrieval_missing_document(temp_settings: Settings) -> None:
    """When a specific document requested for full delivery is missing, return abstention."""
    initialize_database(temp_settings)
    provider = DummyProvider()
    res = ask_question(
        temp_settings,
        question="Give me the complete file content of non_existent_doc.txt",
        top_k=5,
        persist=False,
        llm_provider=provider,
    )
    assert provider.call_count == 0
    assert res["insufficient_evidence"] is True
    assert (
        "does not contain any documents" in res["answer"].lower()
        or "not found" in res["answer"].lower()
    )
    assert res["citations"] == []


def test_conversation_history_intent_with_llm_recap(temp_settings: Settings) -> None:
    """When asking 'What did we just discuss?' with turns, summarize conversation turns."""
    initialize_database(temp_settings)
    with connect(temp_settings) as conn:
        conv = conv_repo.create_conversation(conn, "Recap Thread")
        cid = conv["id"]
        conv_repo.add_message(
            conn, cid, role="user", content="Tell me about MATLAB.", status="completed"
        )
        conv_repo.add_message(
            conn,
            cid,
            role="assistant",
            content="MATLAB is used for matrix math.",
            status="completed",
        )

    provider = DummyProvider(
        '{"answer": "We discussed MATLAB and matrix math.", '
        '"insufficient_evidence": false, "cited_chunk_ids": []}'
    )
    res = ask_question(
        temp_settings,
        question="What did we just discuss?",
        top_k=5,
        conversation_id=cid,
        persist=False,
        llm_provider=provider,
    )

    assert provider.call_count == 1
    assert "Tell me about MATLAB." in provider.last_user_prompt
    assert "MATLAB is used for matrix math." in provider.last_user_prompt
    assert res["answer"] == "We discussed MATLAB and matrix math."
    assert res["archive_context"] == "Conversation history"
