"""Hybrid search orchestration combining semantic vectors and FTS5 lexical ranking."""

from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from typing import Any

from app.core.config import Settings
from app.database.connection import connect, initialize_database
from app.retrieval.embeddings import EmbeddingProvider, get_embedding_provider
from app.retrieval.vector_store import ChromaVectorStore

logger = logging.getLogger("ghostarchive.search")

STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "did",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


def _sanitize_fts_query(query: str) -> str:
    """Extract content terms for FTS5 matching, omitting stopwords and single chars."""
    raw_tokens = re.findall(r"\b[a-zA-Z0-9_]+\b", query)
    tokens = [t for t in raw_tokens if len(t) >= 2 and t.lower() not in STOPWORDS]
    if not tokens:
        tokens = [t for t in raw_tokens if len(t) >= 2]
    if not tokens:
        return ""
    # Safe FTS phrase/token query
    escaped = [f'"{token}"' for token in tokens]
    return " OR ".join(escaped)


def _lexical_search(
    settings: Settings,
    query: str,
    top_k: int,
    document_ids: Sequence[str] | None = None,
) -> dict[str, int]:
    """Return {chunk_id: rank} from SQLite FTS5 index, or empty dict if no matches."""
    fts_expression = _sanitize_fts_query(query)
    if not fts_expression:
        return {}
    try:
        with connect(settings) as connection:
            if document_ids:
                placeholders = ",".join("?" for _ in document_ids)
                sql = f"""
                    SELECT chunk_id, bm25(document_chunks_fts) AS rank_score
                    FROM document_chunks_fts
                    WHERE document_chunks_fts MATCH ?
                      AND document_id IN ({placeholders})
                    ORDER BY rank_score ASC
                    LIMIT ?
                """
                params = [fts_expression, *list(document_ids), top_k]
            else:
                sql = """
                    SELECT chunk_id, bm25(document_chunks_fts) AS rank_score
                    FROM document_chunks_fts
                    WHERE document_chunks_fts MATCH ?
                    ORDER BY rank_score ASC
                    LIMIT ?
                """
                params = [fts_expression, top_k]
            rows = connection.execute(sql, params).fetchall()
            return {row["chunk_id"]: idx for idx, row in enumerate(rows)}
    except Exception as exc:
        logger.warning("FTS search encountered an error: %s", exc)
        return {}


def _ready_chunk_rows(
    settings: Settings,
    chunk_ids: Sequence[str],
    document_ids: Sequence[str],
) -> dict[str, Any]:
    if not chunk_ids:
        return {}
    with connect(settings) as connection:
        placeholders = ",".join("?" for _ in chunk_ids)
        params: list[str] = list(chunk_ids)
        query = f"""
            SELECT c.*, d.original_filename
            FROM document_chunks AS c
            JOIN documents AS d ON d.id = c.document_id
            WHERE c.id IN ({placeholders}) AND d.status = 'ready'
        """
        if document_ids:
            document_placeholders = ",".join("?" for _ in document_ids)
            query += f" AND c.document_id IN ({document_placeholders})"
            params.extend(document_ids)
        rows = connection.execute(query, params).fetchall()
    return {row["id"]: row for row in rows}


def _compute_relevance_label(cosine_similarity: float, lexical_rank: int | None) -> str:
    """Return a readable relevance badge label."""
    if cosine_similarity >= 0.50 or (lexical_rank == 0 and cosine_similarity >= 0.35):
        return "High match"
    if cosine_similarity >= 0.35 or (
        lexical_rank is not None and lexical_rank < 3 and cosine_similarity >= 0.25
    ):
        return "Medium match"
    return "Relevant"


def search_documents(
    settings: Settings,
    query: str,
    top_k: int,
    document_ids: Sequence[str] | None = None,
    *,
    embedding_provider: EmbeddingProvider | None = None,
    vector_store: ChromaVectorStore | None = None,
    min_similarity: float | None = None,
) -> list[dict[str, Any]]:
    """
    Retrieve top-k chunks using hybrid (semantic + lexical FTS5) retrieval
    and calibrated relevance threshold filtering.
    """
    initialize_database(settings)
    threshold = min_similarity if min_similarity is not None else settings.retrieval_min_similarity
    effective_top_k = min(top_k, settings.retrieval_top_k_max)

    provider = embedding_provider or get_embedding_provider(settings.embedding_model)
    store = vector_store or ChromaVectorStore(settings)

    # 1. Semantic retrieval (bounded to effective_top_k)
    result = store.query(
        provider.embed_query(query),
        effective_top_k,
        document_ids,
    )
    raw_ids = result.get("ids", [[]])[0]
    raw_distances = result.get("distances", [[]])[0]

    semantic_ranks: dict[str, int] = {}
    semantic_sims: dict[str, float] = {}
    for idx, (cid, dist) in enumerate(zip(raw_ids, raw_distances, strict=False)):
        sim = float(1.0 - dist)
        semantic_ranks[cid] = idx
        semantic_sims[cid] = sim

    # 2. Lexical retrieval (SQLite FTS5 BM25)
    lexical_ranks: dict[str, int] = {}
    if settings.retrieval_lexical_boost:
        lexical_ranks = _lexical_search(settings, query, effective_top_k, document_ids)

    # 3. Reciprocal Rank Fusion & relevance filtering
    all_candidate_ids = set(semantic_ranks.keys()) | set(lexical_ranks.keys())
    if not all_candidate_ids:
        return []

    rrf_k = 60
    scored_candidates: list[tuple[str, float, float, int | None]] = []
    for cid in all_candidate_ids:
        s_rank = semantic_ranks.get(cid)
        l_rank = lexical_ranks.get(cid)
        sim = semantic_sims.get(cid, 0.0)

        # Calculate RRF score
        rrf_score = 0.0
        if s_rank is not None:
            rrf_score += 1.0 / (rrf_k + s_rank)
        if l_rank is not None:
            rrf_score += 1.0 / (rrf_k + l_rank)

        # Relevance filtering:
        # A result is deemed relevant if:
        # - Cosine similarity meets or exceeds configured threshold (e.g. 0.30)
        # OR
        # - Strong lexical match in top 3 AND positive semantic alignment (>= 0.18)
        is_relevant = (sim >= threshold) or (l_rank is not None and l_rank < 3 and sim >= 0.18)
        if is_relevant:
            scored_candidates.append((cid, rrf_score, sim, l_rank))

    if not scored_candidates:
        return []

    # Sort descending by RRF score, then similarity
    scored_candidates.sort(key=lambda item: (item[1], item[2]), reverse=True)
    selected = scored_candidates[:effective_top_k]
    selected_ids = [item[0] for item in selected]

    # 4. Resolve metadata from authoritative SQLite store
    rows = _ready_chunk_rows(settings, selected_ids, document_ids or [])
    output: list[dict[str, Any]] = []

    for cid, _rrf_score, sim, l_rank in selected:
        row = rows.get(cid)
        if row is None:
            logger.warning("Dropping orphan or non-ready vector: %s", cid)
            continue
        bounded_score = round(max(0.0, min(1.0, sim)), 4)
        output.append(
            {
                "chunk_id": row["id"],
                "document_id": row["document_id"],
                "filename": row["original_filename"],
                "page_number": row["page_number"],
                "text": row["content"],
                "start_char": row["start_char"],
                "end_char": row["end_char"],
                "score": bounded_score,
                "cosine_similarity": round(sim, 4),
                "relevance_label": _compute_relevance_label(sim, l_rank),
            }
        )
    return output
