"""Grounded question-answer orchestration with conversation persistence and idempotency."""

from __future__ import annotations

import json
import re
import sqlite3
import uuid
from collections.abc import Callable, Sequence
from typing import Any

from app.core.config import Settings
from app.core.errors import ErrorCode, GhostArchiveException
from app.database.connection import connect, initialize_database
from app.database.repositories import conversations as conv_repo
from app.database.repositories import documents as doc_repo
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
    conversation_id: str | None = None,
    client_turn_id: str | None = None,
    persist: bool = True,
    search_fn: Callable[..., list[dict[str, Any]]] | None = None,
    ollama_client: OllamaClient | None = None,
    llm_provider: LLMProvider | None = None,
) -> dict[str, Any]:
    """Retrieve evidence, generate a grounded answer, and persist conversational turns."""
    clean_question = question.strip()
    active_search_fn = search_fn or search_documents
    provider = llm_provider or ollama_client or get_llm_provider(settings)
    active_model = getattr(provider, "model_name", settings.ollama_model)
    doc_ids_list = list(document_ids) if document_ids else []

    # Persistence & Concurrency Coordination
    active_conv_id = conversation_id
    active_turn_id = client_turn_id or str(uuid.uuid4())
    asst_msg_id: str | None = None
    recent_turns: list[dict[str, str]] = []

    if persist:
        initialize_database(settings)
        with connect(settings) as conn:
            # 1. Resolve or create conversation
            if active_conv_id:
                conv = conv_repo.get_conversation(conn, active_conv_id)
                if not conv:
                    raise GhostArchiveException(
                        ErrorCode.NOT_FOUND,
                        f"Conversation '{active_conv_id}' does not exist.",
                        404,
                    )
            else:
                default_title = clean_question[:40].strip() or "New Conversation"
                new_conv = conv_repo.create_conversation(conn, default_title)
                active_conv_id = new_conv["id"]

            # 2. Retrieve bounded conversational context (max 3 turns, scope-isolated)
            # Pass exclude_turn_id so neither a retried turn nor a new turn is counted
            recent_turns = conv_repo.get_recent_completed_turns(
                conn,
                active_conv_id,
                limit_turns=3,
                active_scope_ids=doc_ids_list,
                exclude_turn_id=active_turn_id,
            )

            # 3. Check Idempotency and existing turn
            existing_user_msg = conv_repo.get_message_by_turn(
                conn, active_conv_id, active_turn_id, role="user"
            )
            existing_asst_msg = conv_repo.get_message_by_turn(
                conn, active_conv_id, active_turn_id, role="assistant"
            )

            if existing_user_msg:
                # Reject reuse of idempotency key with a different question (HTTP 409)
                if existing_user_msg["content"].strip() != clean_question:
                    raise GhostArchiveException(
                        ErrorCode.CONFLICT,
                        "Idempotency key reused with a different question.",
                        409,
                    )

                if existing_asst_msg:
                    # Idempotent response for completed turn
                    if existing_asst_msg["status"] == "completed":
                        return {
                            "answer": existing_asst_msg["content"],
                            "direct_answer": existing_asst_msg["direct_answer"]
                            or existing_asst_msg["content"],
                            "archive_context": existing_asst_msg["archive_context"],
                            "limitations": existing_asst_msg["limitations"],
                            "insufficient_evidence": existing_asst_msg["insufficient_evidence"],
                            "citations": existing_asst_msg["citations"],
                            "retrieval_count": existing_asst_msg["retrieval_count"],
                            "model": existing_asst_msg["model"] or active_model,
                            "conversation_id": active_conv_id,
                            "message_id": existing_asst_msg["id"],
                            "client_turn_id": active_turn_id,
                        }

                    # Retry flow: failed -> pending
                    if existing_asst_msg["status"] == "failed":
                        asst_msg_id = existing_asst_msg["id"]
                        conv_repo.update_assistant_message(
                            conn, asst_msg_id, status="pending", error_message=None
                        )
                    elif existing_asst_msg["status"] == "pending":
                        # Stale turn recovery check (timeout threshold 60s)
                        pending_turn = conv_repo.check_pending_turn(
                            conn, active_conv_id, timeout_seconds=60
                        )
                        if pending_turn and pending_turn["id"] == existing_asst_msg["id"]:
                            raise GhostArchiveException(
                                ErrorCode.CONFLICT,
                                "A request is already in progress for this turn.",
                                409,
                            )
                        # Reclaimed stale turn, retry
                        asst_msg_id = existing_asst_msg["id"]
                        conv_repo.update_assistant_message(
                            conn, asst_msg_id, status="pending", error_message=None
                        )
            else:
                # Check for active concurrent turn in conversation
                active_pending = conv_repo.check_pending_turn(
                    conn, active_conv_id, timeout_seconds=60
                )
                if active_pending:
                    raise GhostArchiveException(
                        ErrorCode.CONFLICT,
                        "Previous turn in this conversation is still processing. Please wait.",
                        409,
                    )

                # Atomically record user message and pending assistant message
                conv_repo.add_message(
                    conn,
                    active_conv_id,
                    role="user",
                    content=clean_question,
                    status="completed",
                    client_turn_id=active_turn_id,
                    scope_document_ids=doc_ids_list,
                )
                asst_rec = conv_repo.add_message(
                    conn,
                    active_conv_id,
                    role="assistant",
                    content="",
                    status="pending",
                    client_turn_id=active_turn_id,
                    scope_document_ids=doc_ids_list,
                )
                asst_msg_id = asst_rec["id"]
    elif active_conv_id:
        initialize_database(settings)
        with connect(settings) as conn:
            recent_turns = conv_repo.get_recent_completed_turns(
                conn,
                active_conv_id,
                limit_turns=3,
                active_scope_ids=doc_ids_list,
                exclude_turn_id=active_turn_id,
            )

    # Fast intent evaluation
    intent = classify_query_intent(clean_question)

    def _persist_and_return(
        ans: str,
        direct_ans: str,
        ctx: str | None,
        lims: list[str],
        insufficient: bool,
        cits: list[dict[str, Any]],
        retrieval_cnt: int,
    ) -> dict[str, Any]:
        if persist and active_conv_id and asst_msg_id:
            with connect(settings) as conn:
                conv_repo.update_assistant_message(
                    conn,
                    asst_msg_id,
                    status="completed",
                    content=ans,
                    direct_answer=direct_ans,
                    archive_context=ctx,
                    limitations=lims,
                    insufficient_evidence=insufficient,
                    citations=cits,
                    retrieval_count=retrieval_cnt,
                    model=active_model,
                )
                conv_repo.touch_conversation(conn, active_conv_id)
        return {
            "answer": ans,
            "direct_answer": direct_ans,
            "archive_context": ctx,
            "limitations": lims,
            "insufficient_evidence": insufficient,
            "citations": cits,
            "retrieval_count": retrieval_cnt,
            "model": active_model,
            "conversation_id": active_conv_id,
            "message_id": asst_msg_id,
            "client_turn_id": active_turn_id,
        }

    if intent == QueryIntent.GREETING:
        greeting_text = (
            "Hello! I am GhostArchive, your private, evidence-grounded memory assistant. "
            "You can ask me questions about your imported notes, letters, journals, and records, "
            "or ask me to summarize your collection."
        )
        return _persist_and_return(
            ans=greeting_text,
            direct_ans=greeting_text,
            ctx="GhostArchive operates strictly on your locally imported documents.",
            lims=[],
            insufficient=False,
            cits=[],
            retrieval_cnt=0,
        )

    if intent == QueryIntent.ARCHIVE_SUMMARY:
        summary_result = summarize_archive(settings, llm_provider=provider)
        return _persist_and_return(
            ans=summary_result["summary"],
            direct_ans=summary_result["summary"],
            ctx=summary_result["scope"],
            lims=summary_result.get("limitations", []),
            insufficient=False,
            cits=[],
            retrieval_cnt=len(summary_result.get("inspected_documents", [])),
        )

    if intent == QueryIntent.FULL_DOCUMENT_RETRIEVAL:
        with connect(settings) as conn:
            target_docs: list[sqlite3.Row] = []

            # 1. Scoped document_ids explicitly provided
            if document_ids:
                for doc_id in document_ids:
                    row = doc_repo.get_document(conn, doc_id)
                    if row and row["status"] == "ready":
                        target_docs.append(row)

            # 2. No scope, check if question mentions any filename or title
            if not target_docs:
                all_ready_docs = doc_repo.list_documents(conn, status="ready")
                normalized_q = clean_question.lower()
                for doc in all_ready_docs:
                    fname = (doc["original_filename"] or "").lower()
                    title = (doc["title"] or "").lower()
                    if (fname and fname in normalized_q) or (title and title in normalized_q):
                        target_docs.append(doc)

                # 3. If no specific name mentioned, but exactly 1 document exists in archive
                if not target_docs and len(all_ready_docs) == 1:
                    target_docs.append(all_ready_docs[0])

            if not target_docs:
                all_ready_docs = doc_repo.list_documents(conn, status="ready")
                if not all_ready_docs:
                    msg = "The archive does not contain any documents to deliver."
                    return _persist_and_return(
                        ans=msg,
                        direct_ans=msg,
                        ctx=None,
                        lims=["No ready documents exist in the archive."],
                        insufficient=True,
                        cits=[],
                        retrieval_cnt=0,
                    )
                doc_names = ", ".join(f"'{d['original_filename']}'" for d in all_ready_docs[:5])
                more = f" and {len(all_ready_docs) - 5} more" if len(all_ready_docs) > 5 else ""
                msg = (
                    f"Your archive contains multiple documents ({doc_names}{more}). "
                    "Please select a document in the scope filter or specify which document "
                    "you want delivered (e.g. 'Deliver the whole file of sampling theorem.txt')."
                )
                return _persist_and_return(
                    ans=msg,
                    direct_ans=msg,
                    ctx="Multiple documents available in archive.",
                    lims=["Please specify target document by name or select it in document scope."],
                    insufficient=False,
                    cits=[],
                    retrieval_cnt=0,
                )

            # Retrieve complete content and construct chunk citations for target_docs
            doc_texts: list[str] = []
            all_cits: list[dict[str, Any]] = []

            for doc in target_docs:
                chunks = doc_repo.get_chunks(conn, doc["id"])
                storage_path = doc_repo.document_storage_path(settings, doc)

                content = ""
                if doc["file_type"] in ["txt", "md"] and storage_path.exists():
                    try:
                        content = storage_path.read_text(encoding="utf-8")
                    except Exception:
                        content = "\n\n".join(c["content"] for c in chunks)
                else:
                    content = "\n\n".join(c["content"] for c in chunks)

                doc_texts.append(content)

                for c in chunks:
                    all_cits.append(
                        {
                            "chunk_id": c["id"],
                            "document_id": doc["id"],
                            "filename": doc["original_filename"],
                            "document_title": doc["title"] or doc["original_filename"],
                            "page_number": c["page_number"],
                            "excerpt": c["content"][:200],
                            "evidence_type": "direct",
                        }
                    )

            combined_content = "\n\n---\n\n".join(doc_texts)
            doc_titles = ", ".join(d["original_filename"] for d in target_docs)
            ctx = (
                f"Complete verbatim content of {doc_titles} "
                f"({len(all_cits)} chunks, {len(combined_content)} chars)."
            )
            return _persist_and_return(
                ans=combined_content,
                direct_ans=combined_content,
                ctx=ctx,
                lims=["Verbatim original document content delivered without LLM summarization."],
                insufficient=False,
                cits=all_cits,
                retrieval_cnt=len(all_cits),
            )

    if intent == QueryIntent.CONVERSATION_HISTORY:
        if not recent_turns:
            ans = "There are no previous messages in this conversation yet."
            return _persist_and_return(
                ans=ans,
                direct_ans=ans,
                ctx="Conversation history",
                lims=["No prior conversation turns exist to reference."],
                insufficient=False,
                cits=[],
                retrieval_cnt=0,
            )

        q_lower = clean_question.lower()
        if re.search(
            r"\b(?:what\s+was\s+(?:my\s+|the\s+)?(?:previous|last)\s+question)\b", q_lower
        ):
            last_user_turn = next(
                (t["content"] for t in reversed(recent_turns) if t.get("role") == "user"), None
            )
            if last_user_turn:
                ans = f'Your previous question was: "{last_user_turn}"'
                return _persist_and_return(
                    ans=ans,
                    direct_ans=ans,
                    ctx="Conversation history",
                    lims=[],
                    insufficient=False,
                    cits=[],
                    retrieval_cnt=0,
                )

        if re.search(
            r"\b(?:what\s+was\s+(?:your\s+)?(?:last|previous)\s+answer)\b", q_lower
        ) or re.search(r"\b(?:repeat\s+(?:what\s+you\s+said|your\s+last\s+answer))\b", q_lower):
            last_asst_turn = next(
                (t["content"] for t in reversed(recent_turns) if t.get("role") == "assistant"), None
            )
            if last_asst_turn:
                ans = f"My previous answer was:\n\n{last_asst_turn}"
                return _persist_and_return(
                    ans=ans,
                    direct_ans=ans,
                    ctx="Conversation history",
                    lims=[],
                    insufficient=False,
                    cits=[],
                    retrieval_cnt=0,
                )

        history_formatted = "\n".join(
            f"{'User' if t.get('role') == 'user' else 'Assistant'}: {t.get('content', '')}"
            for t in recent_turns
        )
        history_prompt = (
            f"Here is the conversation history:\n\n{history_formatted}\n\n"
            f"Current Question:\n{clean_question}\n\n"
            "Provide a concise, direct summary or response based only on the conversation above. "
            "Return ONLY valid JSON with this schema:\n"
            '{"answer": "Your response based on conversation history", '
            '"archive_context": "Conversation history", "limitations": [], '
            '"insufficient_evidence": false, "cited_chunk_ids": []}'
        )
        try:
            raw = provider.chat(SYSTEM_PROMPT, history_prompt)
            parsed = json.loads(raw.strip())
            ans = str(parsed.get("answer") or parsed.get("direct_answer") or raw.strip())
            ctx = str(parsed.get("archive_context") or "Conversation history")
            lims = (
                [str(x) for x in parsed.get("limitations", [])]
                if isinstance(parsed.get("limitations"), list)
                else []
            )
            return _persist_and_return(
                ans=ans,
                direct_ans=ans,
                ctx=ctx,
                lims=lims,
                insufficient=False,
                cits=[],
                retrieval_cnt=0,
            )
        except Exception:
            fallback_ans = f"In this conversation so far, we discussed:\n\n{history_formatted}"
            return _persist_and_return(
                ans=fallback_ans,
                direct_ans=fallback_ans,
                ctx="Conversation history",
                lims=[],
                insufficient=False,
                cits=[],
                retrieval_cnt=0,
            )

    if intent == QueryIntent.OFF_TOPIC:
        off_topic_msg = (
            "GhostArchive is a personal memory archive assistant designed to search "
            "and summarize your imported records. I cannot generate arbitrary code."
        )
        return _persist_and_return(
            ans=off_topic_msg,
            direct_ans=off_topic_msg,
            ctx=None,
            lims=["Query was identified as outside the scope of archive records."],
            insufficient=True,
            cits=[],
            retrieval_cnt=0,
        )

    # Document retrieval strictly respecting permitted document_ids
    evidence = active_search_fn(settings, clean_question, top_k, document_ids)
    if not evidence:
        msg = "The archive does not contain sufficient evidence."
        return _persist_and_return(
            ans=msg,
            direct_ans=msg,
            ctx=None,
            lims=["No passages in the archive met the relevance criteria."],
            insufficient=True,
            cits=[],
            retrieval_cnt=0,
        )

    # Deterministic mathematical & code reasoning extraction (BUG-10)
    from app.generation.math_reasoning import (
        analyze_code_identifiers,
        analyze_math_question,
        extract_signal_parameters,
    )

    params = extract_signal_parameters(evidence)
    math_result = analyze_math_question(clean_question, params)
    code_result = analyze_code_identifiers(clean_question, evidence)

    # Format bounded prompt with context, quoted evidence, and intent guidance
    user_prompt = build_user_prompt(
        clean_question,
        evidence,
        history=recent_turns,
        intent=str(intent.value),
        math_result=math_result,
        code_result=code_result,
    )

    try:
        raw = provider.chat(SYSTEM_PROMPT, user_prompt)
        validated = validate_model_output(
            raw,
            evidence,
            math_result=math_result,
            code_result=code_result,
        )
    except Exception as exc:
        if persist and asst_msg_id:
            with connect(settings) as conn:
                conv_repo.update_assistant_message(
                    conn,
                    asst_msg_id,
                    status="failed",
                    error_message=str(exc),
                )
        raise

    return _persist_and_return(
        ans=validated["answer"],
        direct_ans=validated.get("direct_answer") or validated["answer"],
        ctx=validated.get("archive_context"),
        lims=validated.get("limitations", []),
        insufficient=validated.get("insufficient_evidence", False),
        cits=validated.get("citations", []),
        retrieval_cnt=len(evidence),
    )
