"""Text normalization and deterministic chunking."""

from __future__ import annotations

import re
from dataclasses import dataclass


def normalize_text(text: str) -> str:
    """Normalize line endings and remove control characters without losing paragraphs."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = "".join(
        character
        for character in normalized
        if character in ("\n", "\t") or not ord(character) < 32
    )
    return normalized.strip()


@dataclass(frozen=True)
class TextChunk:
    """A normalized text chunk and its source offsets."""

    index: int
    content: str
    start_char: int
    end_char: int


def chunk_text(text: str, target_size: int = 900, overlap: int = 120) -> list[TextChunk]:
    """Split text by paragraphs, then bounded overlapping windows for long paragraphs."""
    if not text:
        return []
    if target_size <= overlap:
        raise ValueError("target_size must be greater than overlap")

    paragraphs = [match for match in re.finditer(r"\S(?:.*?\S)?(?=\n\n|\Z)", text, re.S)]
    chunks: list[TextChunk] = []
    current: list[tuple[int, int, str]] = []
    current_length = 0

    def flush() -> None:
        nonlocal current, current_length
        if not current:
            return
        start = current[0][0]
        end = current[-1][1]
        chunks.append(TextChunk(len(chunks), text[start:end], start, end))
        current = []
        current_length = 0

    for paragraph in paragraphs:
        start, end = paragraph.start(), paragraph.end()
        content = paragraph.group()
        if len(content) > target_size:
            flush()
            cursor = start
            while cursor < end:
                raw_window_end = min(cursor + target_size, end)
                if raw_window_end < end:
                    # Break on sentence or space to avoid mid-word cuts
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
                chunks.append(TextChunk(len(chunks), text[cursor:window_end], cursor, window_end))
                if window_end >= end:
                    break
                cursor = max(cursor + 1, window_end - overlap)
            continue
        if current and current_length + len(content) + 2 > target_size:
            flush()
        current.append((start, end, content))
        current_length = end - current[0][0]
    flush()
    return chunks
