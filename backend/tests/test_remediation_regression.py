"""Regression test suite for retrieval reliability, temporal reasoning, and answer quality."""

from __future__ import annotations

from app.core.config import Settings
from app.database.connection import connect, initialize_database
from app.generation.output_validation import validate_model_output
from app.generation.prompts import SYSTEM_PROMPT, build_user_prompt
from app.services.intent_service import QueryIntent, classify_query_intent
from app.services.search_service import (
    _detect_temporal_intent,
    _sanitize_fts_query,
    search_documents,
)


class MockEmbeddingProvider:
    """Deterministic embedding provider for regression tests."""

    def __init__(self, doc_sims: dict[str, float] | None = None) -> None:
        self.doc_sims = doc_sims or {}

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(t))] for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text))]


class MockVectorStore:
    """Mock Chroma vector store allowing configurable cosine distances per chunk."""

    def __init__(self, chunk_distances: dict[str, float] | None = None) -> None:
        self.chunk_distances = chunk_distances or {}

    def query(self, embedding, top_k, document_ids=None):
        ids = list(self.chunk_distances.keys())[:top_k]
        distances = [self.chunk_distances[cid] for cid in ids]
        return {"ids": [ids], "distances": [distances]}


def _create_test_document(
    settings: Settings,
    doc_id: str,
    filename: str,
    content: str,
    *,
    title: str | None = None,
    source_date: str | None = None,
) -> str:
    """Insert a document and its single chunk with FTS indexing."""
    initialize_database(settings)
    chunk_id = f"{doc_id}:chunk:0"
    with connect(settings) as conn:
        conn.execute(
            """
            INSERT INTO documents (
                id, original_filename, stored_filename, content_hash, file_type,
                byte_size, status, title, source_date, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'txt', ?, 'ready', ?, ?, datetime('now'), datetime('now'))
            """,
            (doc_id, filename, f"{doc_id}.txt", doc_id, len(content), title, source_date),
        )
        conn.execute(
            """
            INSERT INTO document_chunks (
                id, document_id, chunk_index, content, start_char, end_char, created_at
            ) VALUES (?, ?, 0, ?, 0, ?, datetime('now'))
            """,
            (chunk_id, doc_id, content, len(content)),
        )
        conn.execute(
            """
            INSERT INTO document_chunks_fts (chunk_id, document_id, filename, content)
            VALUES (?, ?, ?, ?)
            """,
            (chunk_id, doc_id, filename, content),
        )
    return chunk_id


def test_porter_stemming_query_sanitization() -> None:
    """Verify FTS query sanitization leaves alphanumeric tokens unquoted for Porter stemming."""
    sanitized = _sanitize_fts_query("vegetarian mild food preferences")
    # Tokens should not be wrapped in double quotes so SQLite FTS5 porter stemmer operates
    assert '"preferences"' not in sanitized
    assert "preferences" in sanitized
    assert "vegetarian" in sanitized
    assert "food" in sanitized


def test_fts_porter_stemming_retrieval(temp_settings: Settings) -> None:
    """Verify that 'preferences' in the query stems and matches 'preference' in document text."""
    chunk_id = _create_test_document(
        temp_settings,
        "doc-diet",
        "diet.txt",
        "Dietary notes: I have a preference for vegetarian food with mild spices.",
    )
    # Distance 0.75 -> sim 0.25 (positive semantic alignment)
    store = MockVectorStore({chunk_id: 0.75})
    provider = MockEmbeddingProvider()

    results = search_documents(
        temp_settings,
        "vegetarian mild food preferences",
        top_k=5,
        embedding_provider=provider,
        vector_store=store,
    )

    assert len(results) == 1
    assert results[0]["chunk_id"] == chunk_id
    assert "preference" in results[0]["text"]


def test_irrelevant_short_query_rejection(temp_settings: Settings) -> None:
    """Verify that unrelated nearest neighbor vector match with no lexical overlap is rejected."""
    chunk_id = _create_test_document(
        temp_settings,
        "doc-lantern",
        "lantern_arch.md",
        "Lantern project architecture overview: background task queues, FastAPI workers.",
    )
    # Cosine distance 0.69 -> sim 0.31 (rejected by calibrated 0.35 threshold)
    store = MockVectorStore({chunk_id: 0.69})
    provider = MockEmbeddingProvider()

    results = search_documents(
        temp_settings,
        "winter arc",
        top_k=5,
        embedding_provider=provider,
        vector_store=store,
    )

    assert results == []


def test_temporal_intent_detection() -> None:
    """Verify classification of temporal query phrasing."""
    assert (
        _detect_temporal_intent("What is the latest agreed study-group meeting time?") == "latest"
    )
    assert _detect_temporal_intent("most recent decision on database") == "latest"
    assert (
        _detect_temporal_intent("What was the original upload endpoint target date?") == "earliest"
    )
    assert _detect_temporal_intent("show the timeline of changes") == "chronological"
    assert _detect_temporal_intent("Why was OCR excluded?") is None


def test_temporal_ordering_latest_first(temp_settings: Settings) -> None:
    """Verify that 'latest' queries place newer dated passages ahead of older ones."""
    cid_old = _create_test_document(
        temp_settings,
        "doc-old",
        "meeting_may08.txt",
        "Study group note: meeting planned for 08 May at 11:00 AM.",
        source_date="2026-05-08",
    )
    cid_new = _create_test_document(
        temp_settings,
        "doc-new",
        "meeting_may16.txt",
        "Study group update: agreed meeting time is Sunday at 5:30 PM.",
        source_date="2026-05-16",
    )
    # Even if old chunk has slightly closer distance (0.10 vs 0.12),
    # temporal intent 'latest' must prioritize the newer source date.
    store = MockVectorStore({cid_old: 0.10, cid_new: 0.12})
    provider = MockEmbeddingProvider()

    results = search_documents(
        temp_settings,
        "What is the latest agreed study-group meeting time?",
        top_k=5,
        embedding_provider=provider,
        vector_store=store,
    )

    assert len(results) == 2
    assert results[0]["chunk_id"] == cid_new
    assert "Sunday at 5:30 PM" in results[0]["text"]
    assert results[1]["chunk_id"] == cid_old


def test_temporal_ordering_chronological_first(temp_settings: Settings) -> None:
    """Verify that original/chronological queries place older dated passages first."""
    cid_revised = _create_test_document(
        temp_settings,
        "doc-rev",
        "sprint_revised.txt",
        "Upload endpoint revised target date: 20 May 2026.",
        source_date="2026-05-18",
    )
    cid_original = _create_test_document(
        temp_settings,
        "doc-orig",
        "sprint_plan.txt",
        "Upload endpoint original target date: 15 May 2026.",
        source_date="2026-05-01",
    )
    store = MockVectorStore({cid_revised: 0.10, cid_original: 0.12})
    provider = MockEmbeddingProvider()

    results = search_documents(
        temp_settings,
        "What was the original upload endpoint target date, and what was the revised date?",
        top_k=5,
        embedding_provider=provider,
        vector_store=store,
    )

    assert len(results) == 2
    assert results[0]["chunk_id"] == cid_original
    assert "original target date" in results[0]["text"]


def test_build_user_prompt_includes_passage_date() -> None:
    """Verify that passage timestamps are explicitly included in prompt framing."""
    evidence = [
        {
            "chunk_id": "c-1",
            "filename": "meeting.txt",
            "source_date": "2026-05-16",
            "text": "Agreed schedule: Sunday at 5:30 PM.",
        }
    ]
    prompt = build_user_prompt("When do we meet?", evidence)
    assert '<passage id="c-1" source="meeting.txt" date="2026-05-16">' in prompt


def test_system_prompt_principles_cover_isolation_and_multipart() -> None:
    """Verify that system prompt enforces evidence isolation and multi-part completeness."""
    assert "Answer every requested sub-question or field completely" in SYSTEM_PROMPT
    assert "Strict evidence isolation" in SYSTEM_PROMPT
    assert "Temporal clarity" in SYSTEM_PROMPT


def test_citation_title_resolution() -> None:
    """Verify that citation objects propagate document_title with fallback to filename."""
    evidence = [
        {
            "chunk_id": "chunk-101",
            "document_id": "doc-trip",
            "filename": "jaipur_trip.md",
            "title": "Jaipur Summer Itinerary",
            "page_number": 1,
            "text": "Trip dates: 18-20 July. Hotel budget: Rs 2000. Return train: 8:40 PM.",
        }
    ]
    model_raw = (
        '{"answer": "Dates: 18-20 July 2026, budget: ₹2,000/night, return train: 8:40 PM.", '
        '"direct_answer": "Dates: 18-20 July 2026, budget: ₹2,000/night, return train: 8:40 PM.", '
        '"archive_context": "", "limitations": [], "insufficient_evidence": false, '
        '"cited_chunk_ids": ["chunk-101"]}'
    )
    validated = validate_model_output(model_raw, evidence)
    assert validated["insufficient_evidence"] is False
    assert len(validated["citations"]) == 1
    citation = validated["citations"][0]
    assert citation["document_title"] == "Jaipur Summer Itinerary"
    assert citation["filename"] == "jaipur_trip.md"


def test_intent_routing_differentiates_topic_from_overview() -> None:
    """Verify that topic-focused questions are not misrouted to archive-wide summary."""
    assert (
        classify_query_intent("What does this archive say about Redis?")
        == QueryIntent.ARCHIVE_QUESTION
    )
    assert classify_query_intent("What is this archive about?") == QueryIntent.ARCHIVE_SUMMARY
    assert classify_query_intent("tell me about my archive") == QueryIntent.ARCHIVE_SUMMARY
    assert classify_query_intent("hello") == QueryIntent.GREETING
