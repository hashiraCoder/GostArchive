"""Query intent classification for GhostArchive user interactions."""

from __future__ import annotations

import enum
import re


class QueryIntent(enum.StrEnum):
    """Classified category of user prompt."""

    GREETING = "greeting"
    ARCHIVE_SUMMARY = "archive_summary"
    FULL_DOCUMENT_RETRIEVAL = "full_document_retrieval"
    CONVERSATION_HISTORY = "conversation_history"
    CODE_EXPLANATION = "code_explanation"
    MATHEMATICAL_CALCULATION = "mathematical_calculation"
    CROSS_DOCUMENT_SYNTHESIS = "cross_document_synthesis"
    ARCHIVE_QUESTION = "archive_question"
    OFF_TOPIC = "off_topic"


_GREETING_PATTERNS = [
    r"^\s*(?:hi|hello|hey|howdy|greetings|hola)\b",
    r"^\s*(?:good\s+(?:morning|afternoon|evening|day))\b",
    r"^\s*(?:who\s+are\s+you|what\s+are\s+you|what\s+can\s+you\s+do|how\s+do\s+you\s+work|help(?:\s+me)?)\b",
    r"^\s*(?:what\s+is\s+ghostarchive)\b",
]

_FULL_DOCUMENT_PATTERNS = [
    r"\b(?:deliver|give|show|dump|display|get|read|print|provide|fetch)\s+(?:me\s+)?(?:the\s+)?(?:whole|entire|complete|full|raw)\s+(?:file|document|text|content|contents|notes?)\b",
    r"\b(?:whole|entire|complete|full|raw)\s+(?:file|document|text|content|contents)\s+(?:of|for|from)\b",
    r"\b(?:deliver|give|show|dump|display|read|print)\s+(?:the\s+)?(?:entire|whole|complete|full)\s+(?:file|document|text|content|contents)\b",
    r"\b(?:what\s+is\s+the\s+full\s+content\s+of)\b",
    r"\b(?:show|read|print|display)\s+all\s+(?:the\s+)?(?:text|content|contents)\s+(?:of|in|from)\b",
    r"^\s*(?:full\s+document|entire\s+document|whole\s+file|complete\s+file)\s*$",
]

_CONVERSATION_HISTORY_PATTERNS = [
    r"\b(?:what\s+did\s+we\s+(?:just\s+)?(?:discuss|talk\s+about))\b",
    r"\b(?:what\s+was\s+(?:my\s+|the\s+)?(?:previous|last)\s+(?:question|prompt|turn|message))\b",
    r"\b(?:what\s+was\s+(?:your\s+)?(?:last|previous)\s+answer)\b",
    r"\b(?:summarize\s+(?:our\s+|this\s+)?conversation)\b",
    r"\b(?:repeat\s+(?:what\s+you\s+said|your\s+last\s+answer|earlier))\b",
    r"\b(?:what\s+did\s+i\s+(?:just\s+)?ask(?:\s+you)?)\b",
    r"\b(?:explain\s+your\s+previous\s+answer)\b",
    r"\b(?:recap\s+(?:our\s+|this\s+)?conversation)\b",
]

_CODE_EXPLANATION_PATTERNS = [
    r"\b(?:explain\s+(?:the\s+|this\s+)?(?:code|script|program|implementation|function|algorithm|matlab))\b",
    r"\b(?:how\s+does\s+(?:the\s+|this\s+)?(?:code|script|implementation|algorithm)\s+work)\b",
    r"\b(?:walk\s+(?:me\s+)?through\s+(?:the\s+|this\s+)?(?:code|script|implementation))\b",
    r"\b(?:what\s+does\s+this\s+(?:code|script)\s+do)\b",
    r"\b(?:what\s+does\s+[a-zA-Z0-9_]+\s+do)\b",
    r"\b(?:why\s+is\s+[a-zA-Z0-9_\s]+\s+(?:used|called|needed))\b",
    r"\b(?:what\s+is\s+[a-zA-Z0-9_]+\s+used\s+for)\b",
    r"\b(?:what\s+is\s+the\s+purpose\s+of\s+[a-zA-Z0-9_]+)\b",
    r"\b(?:matlab\s+code\s+explanation|explain\s+the\s+matlab)\b",
]

_MATH_CALCULATION_PATTERNS = [
    r"\b(?:calculate|compute|solve)\s+(?:the\s+)?(?:nyquist|frequency|formula|rate|sampling|math|equation|interval)\b",
    r"\b(?:what\s+is\s+(?:the\s+)?nyquist\s+rate\s+(?:for|if|with))\b",
    r"\b(?:how\s+many\s+samples\s+(?:are\s+)?(?:generated|created|calculated))\b",
    r"\b(?:calculate\s+(?:fs|fm|nyquist|sampling))\b",
]

_SYNTHESIS_PATTERNS = [
    r"\b(?:differences?\s+between)\s+.+\s+and\s+.+\b",
    r"\b(?:compare|synthesize|differences?\s+between|contrast)\s+(?:the\s+|all\s+|both\s+)?(?:documents|files|notes|records|sources)\b",
    r"\b(?:across\s+(?:all\s+)?(?:the\s+)?(?:documents|files|archive|notes))\b",
    r"\b(?:compare|contrast|synthesize)\s+[a-zA-Z0-9_\.\-\s]+\s+(?:with|to|and)\s+[a-zA-Z0-9_\.\-\s]+\b",
]

_SUMMARY_PATTERNS = [
    r"\b(?:what\s+(?:does\s+)?this\s+archive\s+says?)\b",
    r"\b(?:what\s+(?:is\s+)?in\s+(?:my\s+|the\s+)?archive)\b",
    r"\b(?:summarize\s+(?:my\s+|the\s+)?archive)\b",
    r"\b(?:summarize\s+(?:all\s+)?(?:my\s+)?documents)\b",
    r"\b(?:give\s+me\s+an\s+overview\s+of\s+(?:my\s+|the\s+)?(?:archive|documents|collection))\b",
    r"\b(?:overview\s+of\s+(?:my\s+|the\s+)?archive)\b",
    r"\b(?:what\s+documents\s+(?:are\s+)?(?:here|in\s+here|uploaded|stored|indexed|available))\b",
    r"\b(?:what\s+have\s+i\s+(?:written|saved|imported|uploaded|stored))\b",
    r"\b(?:what\s+is\s+(?:this|my|the)\s+archive\s+about)\b",
    r"\b(?:tell\s+me\s+about\s+(?:this|my|the)\s+archive)\b",
    r"\b(?:what\s+do\s+i\s+have\s+stored\s+here)\b",
]

_OFF_TOPIC_PATTERNS = [
    r"\b(?:write\s+(?:a\s+)?(?:python|javascript|java|c\+\+|code|script|program))\b",
    r"\b(?:translate\s+(?:this\s+)?to\s+[a-zA-Z]+)\b",
    r"\b(?:tell\s+me\s+a\s+joke)\b",
]


def classify_query_intent(query: str) -> QueryIntent:
    """
    Classify user query into an actionable intent category.

    Deterministic classification ensures consistent routing without
    incurring unnecessary LLM latency for greetings, raw document requests,
    or obvious summaries.
    """
    normalized = query.strip().lower()
    if not normalized:
        return QueryIntent.GREETING

    # 1. Greetings
    for pattern in _GREETING_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return QueryIntent.GREETING

    # 2. Conversation Meta / History Queries
    for pattern in _CONVERSATION_HISTORY_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return QueryIntent.CONVERSATION_HISTORY

    # 3. Full Document Retrieval
    for pattern in _FULL_DOCUMENT_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return QueryIntent.FULL_DOCUMENT_RETRIEVAL

    # 4. Off-Topic Generation Requests
    for pattern in _OFF_TOPIC_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return QueryIntent.OFF_TOPIC

    # 5. Topic-specific queries: e.g. "what does this archive say about Redis?"
    # If the query asks "say about <something>" where <something> is not simply "archive",
    # route to ARCHIVE_QUESTION rather than archive-wide summary.
    topic_match = re.search(
        r"\b(?:say|says|contain|mention|state)\s+about\s+([a-zA-Z0-9_\s]+)",
        normalized,
    )
    if topic_match:
        target = topic_match.group(1).strip()
        if not re.search(r"^(?:this|my|the)?\s*(?:archive|documents|collection)$", target):
            return QueryIntent.ARCHIVE_QUESTION

    # 6. Archive-wide summaries
    for pattern in _SUMMARY_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return QueryIntent.ARCHIVE_SUMMARY

    # 7. Code explanation queries
    for pattern in _CODE_EXPLANATION_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return QueryIntent.CODE_EXPLANATION

    # 8. Mathematical calculation queries
    for pattern in _MATH_CALCULATION_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return QueryIntent.MATHEMATICAL_CALCULATION

    # 9. Cross-document synthesis
    for pattern in _SYNTHESIS_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return QueryIntent.CROSS_DOCUMENT_SYNTHESIS

    # Default: Specific archive question to be retrieved
    return QueryIntent.ARCHIVE_QUESTION
