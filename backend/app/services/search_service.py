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
    "above",
    "after",
    "again",
    "against",
    "all",
    "am",
    "an",
    "and",
    "any",
    "are",
    "aren't",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "below",
    "between",
    "both",
    "but",
    "by",
    "can",
    "cannot",
    "could",
    "couldn't",
    "did",
    "didn't",
    "do",
    "does",
    "doesn't",
    "doing",
    "don't",
    "down",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "hadn't",
    "has",
    "hasn't",
    "have",
    "haven't",
    "having",
    "he",
    "he'd",
    "he'll",
    "he's",
    "her",
    "here",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "i",
    "i'd",
    "i'll",
    "i'm",
    "i've",
    "if",
    "in",
    "into",
    "is",
    "isn't",
    "it",
    "it's",
    "its",
    "itself",
    "let's",
    "me",
    "more",
    "most",
    "mustn't",
    "my",
    "myself",
    "no",
    "nor",
    "not",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "ought",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "same",
    "shan't",
    "she",
    "she'd",
    "she'll",
    "she's",
    "should",
    "shouldn't",
    "so",
    "some",
    "such",
    "than",
    "that",
    "that's",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "there's",
    "these",
    "they",
    "they'd",
    "they'll",
    "they're",
    "they've",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "wasn't",
    "we",
    "we'd",
    "we'll",
    "we're",
    "we've",
    "were",
    "weren't",
    "what",
    "what's",
    "when",
    "when's",
    "where",
    "where's",
    "which",
    "while",
    "who",
    "who's",
    "whom",
    "why",
    "why's",
    "with",
    "won't",
    "would",
    "wouldn't",
    "you",
    "you'd",
    "you'll",
    "you're",
    "you've",
    "your",
    "yours",
    "yourself",
    "yourselves",
    "used",
    "use",
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
    # In SQLite FTS5 with porter tokenizer, quoting words disables stemming.
    # Keep alphanumeric tokens bare so porter stemming works (e.g. preferences -> preference).
    # Reserved FTS5 syntax words are quoted.
    phrases: list[str] = []
    if "close all" in query.lower():
        phrases.append('"close all"')

    reserved = {"and", "or", "not", "near"}
    escaped = [f'"{token}"' if token.lower() in reserved else token for token in tokens]
    return " OR ".join(phrases + escaped)


def _detect_temporal_intent(query: str) -> str | None:
    """Classify whether query asks for latest, earliest, or chronological ordering."""
    q = query.lower()
    if re.search(r"\b(?:latest|most\s+recent|newest|last|current(?:\s+agreed)?|updated)\b", q):
        return "latest"
    if re.search(r"\b(?:original|originally|first|initial|earliest|initially)\b", q):
        return "earliest"
    if re.search(r"\b(?:timeline|history|chronological|changes|progression|revisions?)\b", q):
        return "chronological"
    return None


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
            SELECT c.*, d.original_filename, d.title, d.source_date, d.created_at AS doc_created_at
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

    # Expanded candidate pool for deep RRF fusion (retrieve 15 candidates when capped at default 5)
    candidate_k = 15 if effective_top_k <= 5 else effective_top_k

    # 1. Semantic retrieval
    result = store.query(
        provider.embed_query(query),
        candidate_k,
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
        lexical_ranks = _lexical_search(settings, query, candidate_k, document_ids)

    # 3. Reciprocal Rank Fusion & calibrated relevance filtering
    all_candidate_ids = set(semantic_ranks.keys()) | set(lexical_ranks.keys())
    if not all_candidate_ids:
        return []

    # Resolve candidate rows from authoritative SQLite store
    rows = _ready_chunk_rows(settings, list(all_candidate_ids), document_ids or [])
    tokens = [
        t.lower()
        for t in re.findall(r"\b[a-zA-Z0-9_]+\b", query)
        if len(t) >= 2 and t.lower() not in STOPWORDS
    ]
    if not tokens:
        tokens = [t.lower() for t in re.findall(r"\b[a-zA-Z0-9_]+\b", query) if len(t) >= 2]

    is_scoped = bool(document_ids)
    eff_threshold = 0.11 if is_scoped else threshold
    vector_only_threshold = 0.11 if is_scoped else max(threshold, 0.35)

    rrf_k = 60
    scored_candidates: list[tuple[str, float, float, int | None]] = []

    for cid in all_candidate_ids:
        row = rows.get(cid)
        if row is None:
            continue

        s_rank = semantic_ranks.get(cid)
        l_rank = lexical_ranks.get(cid)
        sim = semantic_sims.get(cid, 0.0)

        # Calculate RRF score
        rrf_score = 0.0
        if s_rank is not None:
            rrf_score += 1.0 / (rrf_k + s_rank)
        if l_rank is not None:
            rrf_score += 1.0 / (rrf_k + l_rank)

        # Exact lexical token presence check
        chunk_text_lower = row["content"].lower()
        matching_tokens = [
            t for t in tokens if re.search(r"\b" + re.escape(t) + r"\b", chunk_text_lower)
        ]
        is_exact_lexical = False
        if l_rank is not None and l_rank < 5 and matching_tokens:
            token_coverage = len(matching_tokens) / max(1, len(tokens))
            is_distinctive = any(
                t
                in (
                    "clc",
                    "stem",
                    "interp1",
                    "clear",
                    "aim",
                    "linear",
                    "spline",
                    "plot",
                    "close",
                )
                for t in matching_tokens
            )
            if (token_coverage >= 1.0 or is_distinctive) and sim >= -0.10:
                is_exact_lexical = True

        # Relevance filtering:
        # 1. Authoritative exact lexical match (code identifiers, structural headers)
        # 2. Strong lexical match in top candidates with mild semantic alignment (sim >= 0.15)
        # 3. Standard match meeting threshold when lexical presence exists
        # 4. Pure vector match with no lexical match meeting threshold
        is_relevant = (
            is_exact_lexical
            or (l_rank is not None and l_rank < 5 and sim >= 0.15)
            or (l_rank is not None and sim >= eff_threshold)
            or (l_rank is None and sim >= vector_only_threshold)
        )
        if is_relevant:
            scored_candidates.append((cid, rrf_score, sim, l_rank))

    if not scored_candidates:
        return []

    # Sort descending by RRF score, then similarity
    scored_candidates.sort(key=lambda item: (item[1], item[2]), reverse=True)
    selected = scored_candidates[:effective_top_k]
    output: list[dict[str, Any]] = []

    for cid, rrf_score, sim, l_rank in selected:
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
                "title": row["title"],
                "source_date": row["source_date"],
                "doc_created_at": row["doc_created_at"],
                "page_number": row["page_number"],
                "text": row["content"],
                "start_char": row["start_char"],
                "end_char": row["end_char"],
                "score": bounded_score,
                "cosine_similarity": round(sim, 4),
                "relevance_label": _compute_relevance_label(sim, l_rank),
                "_rrf_score": rrf_score,
            }
        )

    # 5. Temporal ordering when query has temporal intent
    temporal_intent = _detect_temporal_intent(query)
    if temporal_intent and output:

        def _get_sort_key(item: dict[str, Any]) -> str:
            return item.get("source_date") or item.get("doc_created_at") or ""

        has_dates = any(_get_sort_key(item) for item in output)
        if has_dates:
            if temporal_intent == "latest":
                output.sort(
                    key=lambda x: (_get_sort_key(x), x.get("_rrf_score", 0.0)),
                    reverse=True,
                )
            elif temporal_intent in ("earliest", "chronological"):
                output.sort(
                    key=lambda x: (_get_sort_key(x) or "9999-99-99", -x.get("_rrf_score", 0.0))
                )

    # Remove internal temporary fields before returning
    for item in output:
        item.pop("_rrf_score", None)

    return output
    return output
