"""Text normalization and deterministic chunking."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Invisible formatting, zero-width characters, and non-breaking elements
INVISIBLE_CHARS = (
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\ufeff",  # byte order mark / zero-width no-break space
    "\u2060",  # word joiner
    "\u00ad",  # soft hyphen
)

# Common unicode mathematical operators and typographic glyphs
MATH_AND_TYPO_REPLACEMENTS = {
    "\u2265": " >= ",  # greater-than or equal to
    "\u2264": " <= ",  # less-than or equal to
    "\u2260": " != ",  # not equal to
    "\u2248": " ~= ",  # approximately equal to
    "\u2212": "-",  # minus sign
    "\u00d7": "*",  # multiplication sign
    "\u00f7": "/",  # division sign
    "\u00a0": " ",  # non-breaking space
    "\u201c": '"',  # left double quote
    "\u201d": '"',  # right double quote
    "\u2018": "'",  # left single quote
    "\u2019": "'",  # right single quote
}

# Structural boundary patterns for documents (Markdown headings, text labels, and alternatives)
HEADING_PATTERNS = [
    re.compile(r"^#{1,6}\s+.+$"),  # Markdown #, ##, ###
    re.compile(
        r"^(?:[A-Za-z0-9 _-]{2,30}):(?:\s+.*)?$"
    ),  # Aim:, Theory:, where:, ENTRY: ..., MEETING: ...
    re.compile(r"^and alternative\b", re.IGNORECASE),
]

SCRIPT_BOUNDARY = re.compile(r"^clc;\s*(?:clear;)?", re.IGNORECASE)


def normalize_text(text: str) -> str:
    """Normalize line endings, remove control/zero-width chars, and normalize math glyphs."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    for ch in INVISIBLE_CHARS:
        normalized = normalized.replace(ch, "")

    for k, v in MATH_AND_TYPO_REPLACEMENTS.items():
        normalized = normalized.replace(k, v)

    # Ensure clean spacing around inequality operators (e.g. fs>=2fm -> fs >= 2fm)
    normalized = re.sub(r"([A-Za-z0-9_])([><=!~]=|[><])([A-Za-z0-9_])", r"\1 \2 \3", normalized)

    # Collapse multiple spaces on each line without flattening newlines
    lines = [re.sub(r"[ \t]+", " ", line) for line in normalized.split("\n")]
    normalized = "\n".join(lines)

    # Filter non-printable control characters (< 32 except \n and \t, and 127)
    cleaned = "".join(
        c for c in normalized if c in ("\n", "\t") or not (ord(c) < 32 or ord(c) == 127)
    )
    return cleaned.strip()


@dataclass(frozen=True)
class TextChunk:
    """A normalized text chunk and its source offsets."""

    index: int
    content: str
    start_char: int
    end_char: int


def _is_heading(line: str) -> bool:
    stripped = line.strip()
    return any(p.match(stripped) for p in HEADING_PATTERNS)


def _is_script_start(line: str) -> bool:
    return bool(SCRIPT_BOUNDARY.match(line.strip()))


def chunk_text(text: str, target_size: int = 900, overlap: int = 120) -> list[TextChunk]:
    """Structure-aware chunking preserving sections, code, and alternatives."""
    if not text:
        return []
    if target_size <= overlap:
        raise ValueError("target_size must be greater than overlap")

    # Step 1: Parse text lines into atomic blocks with structural types
    raw_lines = text.split("\n")
    blocks: list[tuple[int, int, str, str]] = []  # (start, end, content, type)

    char_offset = 0
    current_lines: list[str] = []
    current_block_start = 0

    def flush_block(b_type: str = "text") -> None:
        nonlocal current_lines, current_block_start
        if not current_lines:
            return
        content = "\n".join(current_lines).strip()
        if content:
            blocks.append((current_block_start, char_offset - 1, content, b_type))
        current_lines = []

    for line in raw_lines:
        line_len = len(line) + 1  # include \n
        stripped = line.strip()

        if _is_heading(stripped):
            flush_block("text")
            h_start = char_offset
            h_end = char_offset + len(line)
            blocks.append((h_start, h_end, stripped, "heading"))
            current_block_start = char_offset + line_len
        elif _is_script_start(stripped):
            flush_block("text")
            s_start = char_offset
            s_end = char_offset + len(line)
            blocks.append((s_start, s_end, stripped, "script"))
            current_block_start = char_offset + line_len
        elif not stripped:
            flush_block("text")
            current_block_start = char_offset + line_len
        else:
            if not current_lines:
                current_block_start = char_offset
            current_lines.append(line)

        char_offset += line_len

    flush_block("text")

    # Step 2: Assemble blocks into cohesive chunks
    chunks: list[TextChunk] = []
    curr_blocks: list[tuple[int, int, str, str]] = []
    curr_len = 0

    def flush_chunk() -> None:
        nonlocal curr_blocks, curr_len
        if not curr_blocks:
            return
        start = curr_blocks[0][0]
        end = curr_blocks[-1][1]
        content = text[start:end].strip()
        if content:
            chunks.append(TextChunk(len(chunks), content, start, end))
        curr_blocks = []
        curr_len = 0

    for b_start, b_end, b_content, b_type in blocks:
        b_len = len(b_content)

        # Oversized single block: window-slice with sentence boundary preservation
        if b_len > target_size:
            flush_chunk()
            cursor = b_start
            while cursor < b_end:
                raw_window_end = min(cursor + target_size, b_end)
                if raw_window_end < b_end:
                    break_point = -1
                    for delim in (". ", ".\n", "! ", "? ", "\n", " "):
                        candidate = text.rfind(
                            delim, cursor + int(target_size * 0.7), raw_window_end
                        )
                        if candidate != -1:
                            break_point = candidate + len(delim.rstrip())
                            break
                    window_end = break_point if break_point != -1 else raw_window_end
                else:
                    window_end = raw_window_end
                sub_content = text[cursor:window_end].strip()
                if sub_content:
                    chunks.append(TextChunk(len(chunks), sub_content, cursor, window_end))
                if window_end >= b_end:
                    break
                cursor = max(cursor + 1, window_end - overlap)
            continue

        # Keep heading attached to its following body block
        has_only_heading = curr_blocks and all(t == "heading" for _, _, _, t in curr_blocks)

        is_hard_split = False
        if curr_blocks and not has_only_heading:
            if b_type == "script":
                # Isolate standalone code scripts
                is_hard_split = True
            elif b_type == "heading" and (
                b_content.startswith("# ")
                or b_content.startswith("## ")
                or "alternative" in b_content.lower()
            ):
                # Isolate major markdown sections (# and ##) and alternative implementations
                is_hard_split = True
            elif curr_len + b_len + 2 > target_size:
                # Size threshold reached
                is_hard_split = True

        if is_hard_split:
            flush_chunk()

        curr_blocks.append((b_start, b_end, b_content, b_type))
        curr_len = b_end - curr_blocks[0][0]

    flush_chunk()
    return chunks
