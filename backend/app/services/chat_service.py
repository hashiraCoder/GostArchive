"""Grounded question-answer orchestration."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from app.core.config import Settings
from app.generation.ollama_client import OllamaClient
from app.generation.output_validation import validate_model_output
from app.generation.prompts import SYSTEM_PROMPT, build_user_prompt
from app.services.search_service import search_documents


def ask_question(
    settings: Settings,
    question: str,
    top_k: int,
    document_ids: Sequence[str] | None = None,
    *,
    search_fn: Callable[..., list[dict[str, Any]]] = search_documents,
    ollama_client: OllamaClient | None = None,
) -> dict[str, Any]:
    """Retrieve evidence, generate a grounded answer, and resolve citations."""
    evidence = search_fn(settings, question, top_k, document_ids)
    if not evidence:
        msg = "The archive does not contain sufficient evidence."
        return {
            "answer": msg,
            "direct_answer": msg,
            "archive_context": None,
            "limitations": ["No passages in the archive met the relevance criteria."],
            "insufficient_evidence": True,
            "citations": [],
            "retrieval_count": 0,
            "model": settings.ollama_model,
        }
    client = ollama_client or OllamaClient(settings)
    raw = client.chat(SYSTEM_PROMPT, build_user_prompt(question, evidence))
    validated = validate_model_output(raw, evidence)
    return {**validated, "retrieval_count": len(evidence), "model": settings.ollama_model}
