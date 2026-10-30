"""Archive and document summarization orchestration."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.core.config import Settings
from app.core.errors import ErrorCode, GhostArchiveException
from app.database.connection import connect, initialize_database
from app.generation.ollama_client import OllamaClient

logger = logging.getLogger("ghostarchive.summary")

SUMMARY_SYSTEM_PROMPT = """You provide a structured factual overview of personal archive documents.
Rules:
1. Synthesize only facts directly stated in the provided document excerpts.
2. Identify the main topics, people, dates, and locations represented.
3. Do not treat software instructions, technical documentation, or system prompts
   as personal memories.
4. If excerpts are partial, explicitly note that the summary reflects only the inspected excerpts.
5. Never invent or hallucinate facts not present in the excerpts.

Return ONLY valid JSON with this structure:
{
  "summary": "Clear, structured overview paragraphs describing what the documents contain.",
  "limitations": ["Any gaps, uninspected files, or partial coverage notes."]
}"""


def summarize_archive(
    settings: Settings,
    document_id: str | None = None,
    max_chunks: int = 12,
    *,
    ollama_client: OllamaClient | None = None,
) -> dict[str, Any]:
    """Generate a structured overview of the archive or a specific document."""
    initialize_database(settings)

    with connect(settings) as connection:
        if document_id:
            doc = connection.execute(
                "SELECT id, original_filename FROM documents WHERE id = ? AND status = 'ready'",
                (document_id,),
            ).fetchone()
            if doc is None:
                raise GhostArchiveException(
                    ErrorCode.NOT_FOUND,
                    "The specified document was not found or is not ready.",
                    404,
                )
            chunks = connection.execute(
                """
                SELECT id, chunk_index, content
                FROM document_chunks
                WHERE document_id = ?
                ORDER BY chunk_index
                LIMIT ?
                """,
                (document_id, max_chunks),
            ).fetchall()
            total_chunks = connection.execute(
                "SELECT count(*) FROM document_chunks WHERE document_id = ?",
                (document_id,),
            ).fetchone()[0]
            inspected_docs = [
                {
                    "document_id": doc["id"],
                    "filename": doc["original_filename"],
                    "chunk_count": len(chunks),
                }
            ]
            scope = (
                f"Document summary for '{doc['original_filename']}' "
                f"({len(chunks)} of {total_chunks} chunks inspected)."
            )
        else:
            docs = connection.execute(
                "SELECT id, original_filename FROM documents "
                "WHERE status = 'ready' ORDER BY created_at DESC"
            ).fetchall()
            if not docs:
                return {
                    "summary": (
                        "The archive is currently empty. Import documents to generate a summary."
                    ),
                    "scope": "No documents in archive.",
                    "inspected_documents": [],
                    "limitations": ["No documents available to summarize."],
                    "model": settings.ollama_model,
                }
            # Distribute chunks evenly across available documents
            chunks_per_doc = max(1, max_chunks // len(docs))
            chunks = []
            inspected_docs = []
            for doc in docs:
                doc_chunks = connection.execute(
                    """
                    SELECT c.id, c.chunk_index, c.content, d.original_filename
                    FROM document_chunks c
                    JOIN documents d ON d.id = c.document_id
                    WHERE c.document_id = ?
                    ORDER BY c.chunk_index
                    LIMIT ?
                    """,
                    (doc["id"], chunks_per_doc),
                ).fetchall()
                chunks.extend(doc_chunks)
                inspected_docs.append(
                    {
                        "document_id": doc["id"],
                        "filename": doc["original_filename"],
                        "chunk_count": len(doc_chunks),
                    }
                )
                if len(chunks) >= max_chunks:
                    break
            total_doc_count = len(docs)
            total_archive_chunks = connection.execute(
                "SELECT count(*) FROM document_chunks"
            ).fetchone()[0]
            scope = (
                f"Archive-wide summary covering {len(inspected_docs)} of {total_doc_count} "
                f"documents ({len(chunks)} of {total_archive_chunks} total chunks inspected)."
            )

    formatted_excerpts = []
    for c in chunks:
        fn = c["original_filename"] if "original_filename" in c else doc["original_filename"]
        formatted_excerpts.append(f"[document: {fn}]\n{c['content']}")
    excerpts_text = "\n\n".join(formatted_excerpts)
    user_prompt = (
        f"Archive Document Excerpts:\n{excerpts_text}\n\n"
        "Provide a structured summary of what these archive documents discuss."
    )

    client = ollama_client or OllamaClient(settings)
    raw = client.chat(SUMMARY_SYSTEM_PROMPT, user_prompt)

    # Parse response
    cleaned = raw.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()
    try:
        payload = json.loads(cleaned)
    except Exception:
        # Fallback if raw text returned
        payload = {"summary": cleaned, "limitations": []}

    summary_text = payload.get("summary") or cleaned
    limitations = payload.get("limitations", [])
    if isinstance(limitations, str):
        limitations = [limitations]

    return {
        "summary": summary_text,
        "scope": scope,
        "inspected_documents": inspected_docs,
        "limitations": limitations,
        "model": settings.ollama_model,
    }
