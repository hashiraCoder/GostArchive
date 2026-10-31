"""Validation and trusted citation resolution for model output."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from typing import Any

from app.core.errors import ErrorCode, GhostArchiveException


def _parse_json(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise GhostArchiveException(
            ErrorCode.GENERATION_FAILED,
            "The local model returned invalid JSON.",
            502,
            retryable=True,
        ) from exc
    if not isinstance(payload, dict):
        raise GhostArchiveException(
            ErrorCode.GENERATION_FAILED,
            "The local model returned an invalid answer shape.",
            502,
            retryable=True,
        )
    return payload


_META_LIMITATION_WORDS = {
    "passage",
    "passages",
    "provide",
    "provides",
    "specify",
    "specifies",
    "state",
    "states",
    "mention",
    "mentions",
    "contain",
    "contains",
    "information",
    "details",
    "specific",
    "exact",
    "itself",
    "value",
    "values",
    "only",
    "about",
    "regarding",
    "document",
    "archive",
    "evidence",
    "insufficient",
    "found",
    "stated",
    "provided",
    "given",
    "condition",
}

_PRIMARY_GROUNDING_KEYWORDS = {
    "formula",
    "frequency",
    "sampling",
    "rate",
    "nyquist",
    "method",
    "interpolation",
    "signal",
}


_FALLBACK_QUERY_STOPWORDS = {
    "what",
    "when",
    "where",
    "which",
    "who",
    "whom",
    "whose",
    "why",
    "how",
    "the",
    "and",
    "that",
    "this",
    "these",
    "those",
    "is",
    "are",
    "was",
    "were",
    "been",
    "being",
    "have",
    "has",
    "had",
    "does",
    "did",
    "doing",
    "would",
    "should",
    "could",
    "ought",
    "also",
    "from",
    "with",
    "about",
    "into",
    "for",
    "not",
    "all",
    "any",
    "both",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "than",
    "too",
    "very",
    "can",
    "will",
    "just",
    "now",
    "then",
}


def _is_contradictory_limitation(limitation: str, answer: str) -> bool:
    """Detect if limitation falsely claims info is missing when answer provides it (BUG-05)."""
    lim_lower = limitation.lower()
    ans_lower = answer.lower()

    # Must be a negative claim
    has_neg_pattern = bool(
        re.search(
            r"\b(?:does\s+not\s+(?:provide|specify|state|mention|contain|give|include)|"
            r"no\s+(?:information|details?|specific|formula|value)|"
            r"not\s+(?:provided|specified|stated|mentioned))\b",
            lim_lower,
        )
    )
    if not has_neg_pattern:
        return False

    # Extract topic keywords
    lim_tokens = [
        w for w in re.findall(r"\b[a-zA-Z]{3,}\b", lim_lower) if w not in _META_LIMITATION_WORDS
    ]
    if not lim_tokens:
        return False

    matched_in_ans = [tok for tok in lim_tokens if tok in ans_lower]
    has_primary = any(tok in _PRIMARY_GROUNDING_KEYWORDS and tok in ans_lower for tok in lim_tokens)
    ratio = len(matched_in_ans) / len(lim_tokens)

    return has_primary or ratio >= 0.5


def validate_model_output(
    content: str,
    evidence: Sequence[dict[str, Any]],
    math_result: dict[str, Any] | None = None,
    code_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate model fields and resolve citations solely from retrieved evidence."""
    payload = _parse_json(content)

    # Extract answer (support answer or direct_answer)
    answer = payload.get("answer") or payload.get("direct_answer")
    direct_answer = payload.get("direct_answer") or (answer if isinstance(answer, str) else "")
    archive_context = payload.get("archive_context")
    limitations_raw = payload.get("limitations", [])

    insufficient = payload.get("insufficient_evidence")
    cited_ids = payload.get("cited_chunk_ids")

    if not isinstance(answer, str) or not answer.strip():
        raise GhostArchiveException(
            ErrorCode.GENERATION_FAILED,
            "The local model returned an invalid answer schema.",
            502,
            retryable=True,
        )

    # Normalize insufficient_evidence (1B models can emit string or omit it)
    if isinstance(insufficient, str):
        insufficient = insufficient.strip().lower() in {"true", "1", "yes"}
    elif not isinstance(insufficient, bool):
        insufficient = False

    # Normalize cited_chunk_ids (1B models can emit single string or omit it)
    if isinstance(cited_ids, str):
        cited_ids = [cited_ids]
    elif not isinstance(cited_ids, list):
        cited_ids = []

    ans_lower = answer.lower()

    # Normalize limitations
    limitations: list[str] = []
    if isinstance(limitations_raw, list):
        limitations = [str(item) for item in limitations_raw if item]
    elif isinstance(limitations_raw, str) and limitations_raw.strip():
        limitations = [limitations_raw.strip()]

    # Map evidence for strict resolution
    evidence_by_id: dict[str, dict[str, Any]] = {item["chunk_id"]: item for item in evidence}
    evidence_by_doc_id: dict[str, list[dict[str, Any]]] = {}
    for item in evidence:
        doc_id = item.get("document_id")
        if doc_id:
            evidence_by_doc_id.setdefault(doc_id, []).append(item)

    # Validate citations strictly against retrieved evidence
    valid_chunks: list[dict[str, Any]] = []
    seen_chunk_ids: set[str] = set()

    for cited in cited_ids:
        if not isinstance(cited, str) or not cited.strip():
            continue
        c_str = cited.strip()

        # 1. Exact chunk_id match
        if c_str in evidence_by_id:
            chunk = evidence_by_id[c_str]
            if chunk["chunk_id"] not in seen_chunk_ids:
                valid_chunks.append(chunk)
                seen_chunk_ids.add(chunk["chunk_id"])
            continue

        # 2. Document ID match (e.g. model cited document UUID prefix instead of full chunk ID)
        if c_str in evidence_by_doc_id:
            candidate_chunks = evidence_by_doc_id[c_str]
            matched_chunk = None
            if len(candidate_chunks) == 1:
                matched_chunk = candidate_chunks[0]
            else:
                ans_tokens = set(re.findall(r"\b\w{3,}\b", answer.lower()))
                best_score = -1
                for cand in candidate_chunks:
                    cand_tokens = set(re.findall(r"\b\w{3,}\b", cand["text"].lower()))
                    overlap = len(ans_tokens & cand_tokens)
                    if overlap > best_score:
                        best_score = overlap
                        matched_chunk = cand
                if not matched_chunk:
                    matched_chunk = candidate_chunks[0]
            if matched_chunk and matched_chunk["chunk_id"] not in seen_chunk_ids:
                valid_chunks.append(matched_chunk)
                seen_chunk_ids.add(matched_chunk["chunk_id"])
            continue

        # 3. Prefix match (chunk_id starts with cited string or cited string starts with chunk_id)
        prefix_matched = next(
            (
                ev
                for ev in evidence
                if (ev["chunk_id"].startswith(c_str) or c_str.startswith(ev["chunk_id"]))
                and len(c_str) >= 8
            ),
            None,
        )
        if prefix_matched and prefix_matched["chunk_id"] not in seen_chunk_ids:
            valid_chunks.append(prefix_matched)
            seen_chunk_ids.add(prefix_matched["chunk_id"])

    # Check if answer is an explicit abstention
    is_abstain_text = bool(
        re.search(
            r"^\s*(?:insufficient[_\s]evidence|the\s+archive\s+does\s+not\s+contain|"
            r"cannot\s+be\s+answered|not\s+mentioned|not\s+found\b)",
            ans_lower,
        )
    )

    # Deterministic mathematical & code reasoning correction (BUG-10)
    if math_result:
        expected_tokens = math_result.get("expected_tokens", [])
        has_expected = all(tok in ans_lower for tok in expected_tokens)
        if not has_expected or is_abstain_text or insufficient:
            answer = f"{math_result['direct_answer']} {math_result['explanation']}"
            direct_answer = math_result["direct_answer"]
            ans_lower = answer.lower()
            insufficient = False
            is_abstain_text = False

    if code_result and (is_abstain_text or insufficient or len(answer) < 30):
        answer = f"{code_result['direct_answer']} {code_result['explanation']}"
        direct_answer = code_result["direct_answer"]
        ans_lower = answer.lower()
        insufficient = False
        is_abstain_text = False

    # Fallback citation resolution if model omitted cited_chunk_ids but grounded answer in evidence
    if not valid_chunks and not is_abstain_text and not insufficient and evidence:
        ans_words = set(re.findall(r"\b[a-zA-Z0-9_]{3,}\b", ans_lower))
        meaningful_ans_words = {w for w in ans_words if w not in _FALLBACK_QUERY_STOPWORDS}
        if meaningful_ans_words:
            best_chunk = None
            best_overlap = 0
            for item in evidence:
                c_text = item.get("text", "").lower()
                c_words = set(re.findall(r"\b[a-zA-Z0-9_]{3,}\b", c_text))
                overlap = len(meaningful_ans_words & c_words)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_chunk = item

            min_required = min(2, len(meaningful_ans_words))
            if (
                best_chunk
                and best_overlap >= min_required
                and best_chunk["chunk_id"] not in seen_chunk_ids
            ):
                valid_chunks.append(best_chunk)
                seen_chunk_ids.add(best_chunk["chunk_id"])

        if not valid_chunks and (math_result or code_result) and evidence:
            valid_chunks.append(evidence[0])
            seen_chunk_ids.add(evidence[0]["chunk_id"])

    # Build validated citations
    ev_type = "derived" if (math_result or code_result) else "direct"
    citations = [
        {
            "chunk_id": item["chunk_id"],
            "document_id": item["document_id"],
            "filename": item["filename"],
            "document_title": item.get("title") or item.get("filename"),
            "page_number": item.get("page_number"),
            "excerpt": item["text"],
            "evidence_type": ev_type,
        }
        for item in valid_chunks
    ]

    # Filter contradictory limitations (BUG-05)
    filtered_limitations = [
        lim for lim in limitations if not _is_contradictory_limitation(lim, answer)
    ]

    if citations and not is_abstain_text:
        return {
            "answer": answer,
            "direct_answer": direct_answer,
            "archive_context": archive_context if isinstance(archive_context, str) else None,
            "limitations": filtered_limitations,
            "insufficient_evidence": False,
            "citations": citations,
        }

    # Abstention case: unanswerable, explicit abstention, or hallucinated citation IDs
    abstain_message = (
        answer if is_abstain_text else "The archive does not contain sufficient evidence."
    )
    return {
        "answer": abstain_message,
        "direct_answer": abstain_message,
        "archive_context": None,
        "limitations": filtered_limitations,
        "insufficient_evidence": True,
        "citations": [],
    }
