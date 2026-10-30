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


def validate_model_output(
    content: str,
    evidence: Sequence[dict[str, Any]],
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

    if (
        not isinstance(answer, str)
        or not isinstance(insufficient, bool)
        or not isinstance(cited_ids, list)
    ):
        raise GhostArchiveException(
            ErrorCode.GENERATION_FAILED,
            "The local model returned an invalid answer schema.",
            502,
            retryable=True,
        )

    # Normalize limitations
    limitations: list[str] = []
    if isinstance(limitations_raw, list):
        limitations = [str(item) for item in limitations_raw if item]
    elif isinstance(limitations_raw, str) and limitations_raw.strip():
        limitations = [limitations_raw.strip()]

    # Validate citations strictly against retrieved evidence
    evidence_by_id = {item["chunk_id"]: item for item in evidence}
    valid_ids = [
        chunk_id
        for chunk_id in cited_ids
        if isinstance(chunk_id, str) and chunk_id in evidence_by_id
    ]

    citations = [
        {
            "chunk_id": item["chunk_id"],
            "document_id": item["document_id"],
            "filename": item["filename"],
            "document_title": item.get("filename"),
            "page_number": item.get("page_number"),
            "excerpt": item["text"],
            "evidence_type": "direct",
        }
        for chunk_id in valid_ids
        for item in [evidence_by_id[chunk_id]]
    ]

    if valid_ids and not insufficient:
        return {
            "answer": answer,
            "direct_answer": direct_answer,
            "archive_context": archive_context if isinstance(archive_context, str) else None,
            "limitations": limitations,
            "insufficient_evidence": False,
            "citations": citations,
        }

    # Abstention case: unanswerable or hallucinated citation IDs
    abstain_message = (
        answer if insufficient else "The archive does not contain sufficient evidence."
    )
    return {
        "answer": abstain_message,
        "direct_answer": abstain_message,
        "archive_context": None,
        "limitations": limitations,
        "insufficient_evidence": True,
        "citations": [],
    }
