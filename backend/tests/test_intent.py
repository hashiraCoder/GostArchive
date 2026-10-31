"""Unit tests for query intent classification."""

from __future__ import annotations

import pytest

from app.services.intent_service import QueryIntent, classify_query_intent


@pytest.mark.parametrize(
    ("query", "expected_intent"),
    [
        ("hello", QueryIntent.GREETING),
        ("hi there", QueryIntent.GREETING),
        ("good morning", QueryIntent.GREETING),
        ("who are you?", QueryIntent.GREETING),
        ("what can you do?", QueryIntent.GREETING),
        ("what is ghostarchive?", QueryIntent.GREETING),
        # Archive summaries
        ("what this archive says", QueryIntent.ARCHIVE_SUMMARY),
        ("what is in my archive?", QueryIntent.ARCHIVE_SUMMARY),
        ("summarize my archive", QueryIntent.ARCHIVE_SUMMARY),
        ("give me an overview of my documents", QueryIntent.ARCHIVE_SUMMARY),
        ("what documents are here?", QueryIntent.ARCHIVE_SUMMARY),
        ("what have I written?", QueryIntent.ARCHIVE_SUMMARY),
        ("What is this archive about?", QueryIntent.ARCHIVE_SUMMARY),
        ("tell me about my archive", QueryIntent.ARCHIVE_SUMMARY),
        ("what do I have stored here?", QueryIntent.ARCHIVE_SUMMARY),
        # Full document delivery
        ("deliver the whole file content to me", QueryIntent.FULL_DOCUMENT_RETRIEVAL),
        ("give me the complete file content", QueryIntent.FULL_DOCUMENT_RETRIEVAL),
        ("show me the entire text of the document", QueryIntent.FULL_DOCUMENT_RETRIEVAL),
        ("dump the raw file", QueryIntent.FULL_DOCUMENT_RETRIEVAL),
        ("what is the full content of sampling theorem.txt", QueryIntent.FULL_DOCUMENT_RETRIEVAL),
        ("display the entire document", QueryIntent.FULL_DOCUMENT_RETRIEVAL),
        ("full document", QueryIntent.FULL_DOCUMENT_RETRIEVAL),
        # Conversation history
        ("what did we just discuss?", QueryIntent.CONVERSATION_HISTORY),
        ("what was my previous question?", QueryIntent.CONVERSATION_HISTORY),
        ("what was your last answer?", QueryIntent.CONVERSATION_HISTORY),
        ("summarize our conversation", QueryIntent.CONVERSATION_HISTORY),
        ("repeat what you said earlier", QueryIntent.CONVERSATION_HISTORY),
        ("explain your previous answer", QueryIntent.CONVERSATION_HISTORY),
        ("what did I ask you?", QueryIntent.CONVERSATION_HISTORY),
        ("recap this conversation", QueryIntent.CONVERSATION_HISTORY),
        # Code explanation
        ("explain the MATLAB script", QueryIntent.CODE_EXPLANATION),
        ("explain this code", QueryIntent.CODE_EXPLANATION),
        ("what does this script do?", QueryIntent.CODE_EXPLANATION),
        ("walk me through the code implementation", QueryIntent.CODE_EXPLANATION),
        ("how does this code work?", QueryIntent.CODE_EXPLANATION),
        # Mathematical calculation
        ("calculate the Nyquist rate for 500 Hz", QueryIntent.MATHEMATICAL_CALCULATION),
        ("what is the Nyquist rate for 100 Hz?", QueryIntent.MATHEMATICAL_CALCULATION),
        ("calculate the sampling frequency", QueryIntent.MATHEMATICAL_CALCULATION),
        ("how many samples are generated?", QueryIntent.MATHEMATICAL_CALCULATION),
        ("compute the sampling interval", QueryIntent.MATHEMATICAL_CALCULATION),
        # Cross document synthesis
        ("compare the documents", QueryIntent.CROSS_DOCUMENT_SYNTHESIS),
        (
            "what are the differences between document A and document B?",
            QueryIntent.CROSS_DOCUMENT_SYNTHESIS,
        ),
        ("synthesize findings across all documents", QueryIntent.CROSS_DOCUMENT_SYNTHESIS),
        # Specific archive question
        ("what does this archive say about Redis?", QueryIntent.ARCHIVE_QUESTION),
        ("what is winter arc?", QueryIntent.ARCHIVE_QUESTION),
        ("when did the garden flooded?", QueryIntent.ARCHIVE_QUESTION),
        ("what was the doctor prescription in 1912?", QueryIntent.ARCHIVE_QUESTION),
        ("find the passage where I discussed drainage", QueryIntent.ARCHIVE_QUESTION),
        ("what is the sampling theorem?", QueryIntent.ARCHIVE_QUESTION),
        ("what does clc do?", QueryIntent.CODE_EXPLANATION),
        ("why is clear used?", QueryIntent.CODE_EXPLANATION),
        ("what does interp1 do?", QueryIntent.CODE_EXPLANATION),
        ("what is fm in the code?", QueryIntent.ARCHIVE_QUESTION),
        # Off topic
        ("write a python script to parse csv", QueryIntent.OFF_TOPIC),
        ("tell me a joke", QueryIntent.OFF_TOPIC),
    ],
)
def test_classify_query_intent(query: str, expected_intent: QueryIntent) -> None:
    assert classify_query_intent(query) == expected_intent
