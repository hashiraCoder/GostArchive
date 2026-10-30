"""Remediation regression tests for GhostArchive RAG retrieval and answer quality."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.database.connection import connect, initialize_database
from app.database.repositories.documents import insert_document
from app.generation.output_validation import validate_model_output
from app.services.chat_service import ask_question
from app.services.search_service import search_documents


class MockOllama:
    def __init__(self, response: str) -> None:
        self.response = response
        self.call_count = 0

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        self.call_count += 1
        return self.response


def _setup_test_archive(settings: Settings) -> None:
    initialize_database(settings)
    doc1 = {
        "id": "doc-winter",
        "original_filename": "winter_journal_1923.md",
        "stored_filename": "winter_1923.md",
        "content_hash": "hash_winter",
        "file_type": "md",
        "byte_size": 200,
        "status": "ready",
        "title": "Winter Journal",
        "source_date": "1923-12-01",
        "created_at": "2026-10-30T00:00:00",
        "updated_at": "2026-10-30T00:00:00",
        "error_code": None,
    }
    chunks1 = [
        {
            "id": "doc-winter:0",
            "document_id": "doc-winter",
            "chunk_index": 0,
            "content": "December 1923: A bitter winter has settled on the valley.",
            "page_number": 1,
            "start_char": 0,
            "end_char": 56,
            "created_at": "2026-10-30T00:00:00",
        }
    ]
    doc2 = {
        "id": "doc-conflict",
        "original_filename": "conflicting_accounts.txt",
        "stored_filename": "conflict.txt",
        "content_hash": "hash_conflict",
        "file_type": "txt",
        "byte_size": 250,
        "status": "ready",
        "title": "Conflicting Accounts",
        "source_date": "1923-12-05",
        "created_at": "2026-10-30T00:00:00",
        "updated_at": "2026-10-30T00:00:00",
        "error_code": None,
    }
    chunks2 = [
        {
            "id": "doc-conflict:0",
            "document_id": "doc-conflict",
            "chunk_index": 0,
            "content": "The register states the lower meadow belongs to the church since 1874.",
            "page_number": None,
            "start_char": 0,
            "end_char": 70,
            "created_at": "2026-10-30T00:00:00",
        }
    ]
    with connect(settings) as connection:
        insert_document(connection, doc1, chunks1)
        insert_document(connection, doc2, chunks2)


def test_irrelevant_query_abstains_with_empty_results(temp_settings: Settings) -> None:
    """Out-of-domain query 'what is winter arc' returns 0 results and abstains."""
    _setup_test_archive(temp_settings)

    class OutOfDomainProvider:
        def embed_query(self, text: str) -> list[float]:
            return [0.0]

    class DistantStore:
        def query(self, embedding, top_k, document_ids=None):
            # Distance 0.90 -> Cosine similarity 0.10, well below threshold 0.30
            return {"ids": [["doc-winter:0"]], "distances": [[0.90]]}

    results = search_documents(
        temp_settings,
        "what is winter arc",
        5,
        embedding_provider=OutOfDomainProvider(),
        vector_store=DistantStore(),
    )
    assert results == []

    model = MockOllama("{}")
    chat_result = ask_question(
        temp_settings,
        "what is winter arc",
        5,
        search_fn=lambda *args: [],
        ollama_client=model,
    )
    assert chat_result["insufficient_evidence"] is True
    assert chat_result["citations"] == []
    assert model.call_count == 0


def test_relevant_query_retrieves_correct_passage(temp_settings: Settings) -> None:
    """Relevant query retrieves winter passage and marks relevance."""
    _setup_test_archive(temp_settings)

    class RelevantProvider:
        def embed_query(self, text: str) -> list[float]:
            return [1.0]

    class CloseStore:
        def query(self, embedding, top_k, document_ids=None):
            # Distance 0.35 -> Cosine similarity 0.65 (High match)
            return {"ids": [["doc-winter:0"]], "distances": [[0.35]]}

    results = search_documents(
        temp_settings,
        "winter valley bitter cold",
        5,
        embedding_provider=RelevantProvider(),
        vector_store=CloseStore(),
    )
    assert len(results) == 1
    assert results[0]["filename"] == "winter_journal_1923.md"
    assert results[0]["relevance_label"] in ("High match", "Medium match")
    assert results[0]["cosine_similarity"] > 0.50
    assert results[0]["page_number"] == 1


def test_invalid_and_hallucinated_citations_are_dropped(temp_settings: Settings) -> None:
    """Model-invented chunk IDs are strictly stripped from final citations."""
    evidence = [
        {
            "chunk_id": "real-chunk-1",
            "document_id": "doc-1",
            "filename": "real.txt",
            "page_number": 2,
            "text": "True historical statement.",
        }
    ]
    raw_response = (
        '{"answer": "Here is the answer.", "insufficient_evidence": false, '
        '"cited_chunk_ids": ["real-chunk-1", "invented-chunk-999"]}'
    )
    validated = validate_model_output(raw_response, evidence)
    assert validated["insufficient_evidence"] is False
    assert len(validated["citations"]) == 1
    assert validated["citations"][0]["chunk_id"] == "real-chunk-1"
    assert validated["citations"][0]["document_title"] == "real.txt"
    assert validated["citations"][0]["page_number"] == 2


def test_conflicting_accounts_prompt_framing() -> None:
    """Output validation preserves limitations notes on conflicting accounts."""
    evidence = [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "filename": "source1.txt",
            "page_number": None,
            "text": "Account A: happened in 1874.",
        },
        {
            "chunk_id": "c2",
            "document_id": "d2",
            "filename": "source2.txt",
            "page_number": None,
            "text": "Account B: happened in 1890.",
        },
    ]
    raw = (
        '{"answer": "Accounts differ on the date.", '
        '"archive_context": "One document says 1874 while another says 1890.", '
        '"limitations": ["Sources disagree on the date."], "insufficient_evidence": false, '
        '"cited_chunk_ids": ["c1", "c2"]}'
    )
    validated = validate_model_output(raw, evidence)
    assert validated["insufficient_evidence"] is False
    assert len(validated["citations"]) == 2
    assert "Sources disagree" in validated["limitations"][0]


def test_search_api_no_negative_percentages(temp_settings: Settings, client: TestClient) -> None:
    """The search API endpoint returns non-negative scores and valid relevance labels."""
    _setup_test_archive(temp_settings)
    resp = client.post("/api/search", json={"query": "winter", "top_k": 5})
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["score"] >= 0.0
        assert item["cosine_similarity"] >= -1.0
        assert item["relevance_label"] in ("High match", "Medium match", "Relevant")
