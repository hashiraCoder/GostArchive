"""Grounded question-answer orchestration."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from app.core.config import Settings
from app.generation.ollama_client import OllamaClient
from app.generation.output_validation import validate_model_output
from app.generation.prompts import SYSTEM_PROMPT, build_user_prompt
from app.generation.provider import LLMProvider, get_llm_provider
from app.services.intent_service import QueryIntent, classify_query_intent
from app.services.search_service import search_documents
from app.services.summary_service import summarize_archive


def ask_question(
    settings: Settings,
    question: str,
    top_k: int,
    document_ids: Sequence[str] | None = None,
    *,
    search_fn: Callable[..., list[dict[str, Any]]] = search_documents,
    ollama_client: OllamaClient | None = None,
    llm_provider: LLMProvider | None = None,
) -> dict[str, Any]:
    """Retrieve evidence, generate a grounded answer, and resolve citations."""
    provider = llm_provider or ollama_client or get_llm_provider(settings)
    active_model = getattr(provider, "model_name", settings.ollama_model)
    intent = classify_query_intent(question)

    if intent == QueryIntent.GREETING:
        greeting_text = (
            "Hello! I am GhostArchive, your private, evidence-grounded memory assistant. "
            "You can ask me questions about your imported notes, letters, journals, and records, "
            "or ask me to summarize your collection."
        )
        return {
            "answer": greeting_text,
            "direct_answer": greeting_text,
            "archive_context": (
                "GhostArchive operates strictly on your locally imported documents."
            ),
            "limitations": [],
            "insufficient_evidence": False,
            "citations": [],
            "retrieval_count": 0,
            "model": active_model,
        }

    if intent == QueryIntent.ARCHIVE_SUMMARY:
        summary_result = summarize_archive(settings, llm_provider=provider)
        return {
            "answer": summary_result["summary"],
            "direct_answer": summary_result["summary"],
            "archive_context": summary_result["scope"],
            "limitations": summary_result.get("limitations", []),
            "insufficient_evidence": False,
            "citations": [],
            "retrieval_count": len(summary_result.get("inspected_documents", [])),
            "model": active_model,
        }

    if intent == QueryIntent.OFF_TOPIC:
        off_topic_msg = (
            "GhostArchive is a personal memory archive assistant designed to search "
            "and summarize your imported records. I cannot generate arbitrary code."
        )
        return {
            "answer": off_topic_msg,
            "direct_answer": off_topic_msg,
            "archive_context": None,
            "limitations": ["Query was identified as outside the scope of archive records."],
            "insufficient_evidence": True,
            "citations": [],
            "retrieval_count": 0,
            "model": active_model,
        }

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
            "model": active_model,
        }
    raw = provider.chat(SYSTEM_PROMPT, build_user_prompt(question, evidence))
    validated = validate_model_output(raw, evidence)
    return {**validated, "retrieval_count": len(evidence), "model": active_model}
