"""Phase 5 verification: Grounded Generation, Evidence Adherence, and Contradiction Prevention."""

from __future__ import annotations

import pytest

from app.generation.output_validation import validate_model_output


@pytest.fixture
def sample_evidence() -> list[dict[str, str | int | None]]:
    return [
        {
            "chunk_id": "doc-uuid-1:0:0-483",
            "document_id": "doc-uuid-1",
            "filename": "sampling_theorem.txt",
            "title": "Sampling Theorem",
            "page_number": 1,
            "text": "Aim: To verify the sampling theorem. Formula: fs >= 2fm.",
        },
        {
            "chunk_id": "doc-uuid-1:1:485-1321",
            "document_id": "doc-uuid-1",
            "filename": "sampling_theorem.txt",
            "title": "Sampling Theorem",
            "page_number": 1,
            "text": "clc; clear; close all;\n% Message signal frequency\nfm = 5;\nfs = 20;",
        },
        {
            "chunk_id": "doc-uuid-2:0:0-300",
            "document_id": "doc-uuid-2",
            "filename": "notes.txt",
            "title": "Lab Notes",
            "page_number": 1,
            "text": "Conducted in Lab 4.",
        },
    ]


def test_bug_05_contradictory_limitations_suppressed(
    sample_evidence: list[dict[str, str | int | None]],
) -> None:
    """BUG-05: When model provides answer but hallucinates contradictory limitation, suppress."""
    raw_json = """{
      "answer": "The maximum frequency of the message signal is 5 Hz.",
      "direct_answer": "The maximum frequency of the message signal is 5 Hz.",
      "archive_context": "From MATLAB code.",
      "limitations": [
        "The passage does not provide a specific value for the message frequency.",
        "The passage does not provide the lab instructor name."
      ],
      "insufficient_evidence": true,
      "cited_chunk_ids": ["doc-uuid-1:1:485-1321"]
    }"""

    res = validate_model_output(raw_json, sample_evidence)

    # 1. Answer is preserved
    assert res["answer"] == "The maximum frequency of the message signal is 5 Hz."
    assert res["insufficient_evidence"] is False

    # 2. Valid citation retained
    assert len(res["citations"]) == 1
    assert res["citations"][0]["chunk_id"] == "doc-uuid-1:1:485-1321"

    # 3. Contradictory limitation suppressed, but genuine non-contradictory limitation kept
    assert len(res["limitations"]) == 1
    assert "lab instructor" in res["limitations"][0].lower()
    assert not any("frequency" in lim.lower() for lim in res["limitations"])


def test_document_id_prefix_citation_resolution(
    sample_evidence: list[dict[str, str | int | None]],
) -> None:
    """When 1B model emits document UUID rather than full chunk ID, resolve to matching chunk."""
    raw_json = """{
      "answer": "To verify the sampling theorem.",
      "direct_answer": "To verify the sampling theorem.",
      "archive_context": "The aim of the experiment.",
      "limitations": [],
      "insufficient_evidence": false,
      "cited_chunk_ids": ["doc-uuid-1"]
    }"""

    res = validate_model_output(raw_json, sample_evidence)

    assert res["insufficient_evidence"] is False
    assert len(res["citations"]) == 1
    assert res["citations"][0]["chunk_id"] == "doc-uuid-1:0:0-483"
    assert res["citations"][0]["filename"] == "sampling_theorem.txt"


def test_hallucinated_citation_blocks_ungrounded_answer(
    sample_evidence: list[dict[str, str | int | None]],
) -> None:
    """When model hallucinates an answer citing fake chunk IDs, validation blocks hallucination."""
    raw_json = """{
      "answer": "The faculty instructor is Dr. Eleanor Vance.",
      "direct_answer": "The faculty instructor is Dr. Eleanor Vance.",
      "archive_context": "Physics department.",
      "limitations": [],
      "insufficient_evidence": false,
      "cited_chunk_ids": ["archive_data_1", "fake-uuid-999"]
    }"""

    res = validate_model_output(raw_json, sample_evidence)

    # Hallucinated citations must result in clean insufficient evidence abstention
    assert res["insufficient_evidence"] is True
    assert res["answer"] == "The archive does not contain sufficient evidence."
    assert res["citations"] == []


def test_explicit_abstention_preserved(
    sample_evidence: list[dict[str, str | int | None]],
) -> None:
    """When model outputs explicit abstention, validation preserves abstention cleanly."""
    raw_json = """{
      "answer": "insufficient_evidence",
      "direct_answer": "insufficient_evidence",
      "archive_context": null,
      "limitations": ["The passage does not provide the student's roll number."],
      "insufficient_evidence": true,
      "cited_chunk_ids": []
    }"""

    res = validate_model_output(raw_json, sample_evidence)

    assert res["insufficient_evidence"] is True
    assert res["citations"] == []
    assert len(res["limitations"]) == 1
    assert "roll number" in res["limitations"][0].lower()


def test_mathematical_formula_contradiction_suppression(
    sample_evidence: list[dict[str, str | int | None]],
) -> None:
    """Formula stated in answer suppresses contradictory limitation claiming no formula exists."""
    raw_json = """{
      "answer": "The formula for the sampling theorem is fs >= 2fm.",
      "direct_answer": "The formula for the sampling theorem is fs >= 2fm.",
      "archive_context": "Theory section.",
      "limitations": [
        "The passage does not provide a formula itself, only the condition."
      ],
      "insufficient_evidence": false,
      "cited_chunk_ids": ["doc-uuid-1:0:0-483"]
    }"""

    res = validate_model_output(raw_json, sample_evidence)

    assert res["insufficient_evidence"] is False
    assert len(res["citations"]) == 1
    # Contradictory limitation claiming no formula was provided is suppressed
    assert len(res["limitations"]) == 0


def test_schema_normalization_omitted_keys(
    sample_evidence: list[dict[str, str | int | None]],
) -> None:
    """When a 1B model outputs JSON with only 'answer' key, normalize schema without 502 error."""
    raw_json = '{"answer": "clc; clear; close all;"}'

    res = validate_model_output(raw_json, sample_evidence)

    assert res["insufficient_evidence"] is False
    assert "clc" in res["answer"]
    # Fallback citation links to Chunk 1 which contains 'clc; clear; close all;'
    assert len(res["citations"]) == 1
    assert res["citations"][0]["chunk_id"] == "doc-uuid-1:1:485-1321"


def test_fallback_citation_blocks_hallucination(
    sample_evidence: list[dict[str, str | int | None]],
) -> None:
    """When model omits cited_chunk_ids and hallucinates unevidenced facts, fallback blocks."""
    raw_json = '{"answer": "The experiment was conducted on Mars by astronaut Mark Watney."}'

    res = validate_model_output(raw_json, sample_evidence)

    assert res["insufficient_evidence"] is True
    assert res["answer"] == "The archive does not contain sufficient evidence."
    assert res["citations"] == []
