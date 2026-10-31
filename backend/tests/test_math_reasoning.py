"""Phase 6 verification: Deterministic Mathematical and Code Reasoning."""

from __future__ import annotations

import pytest

from app.generation.math_reasoning import (
    analyze_code_identifiers,
    analyze_math_question,
    extract_signal_parameters,
)
from app.generation.output_validation import validate_model_output


@pytest.fixture
def sampling_evidence() -> list[dict[str, str | int | None]]:
    return [
        {
            "chunk_id": "doc-uuid-1:0:0-483",
            "document_id": "doc-uuid-1",
            "filename": "sampling theorem.txt",
            "title": "Sampling Theorem",
            "page_number": 1,
            "text": (
                "Aim: To verify the sampling theorem.\n"
                "Theory: Continuous signal recovered if fs >= 2*fm.\n"
                "Nyquist rate = 2*fm."
            ),
        },
        {
            "chunk_id": "doc-uuid-1:1:485-1321",
            "document_id": "doc-uuid-1",
            "filename": "sampling theorem.txt",
            "title": "Sampling Theorem",
            "page_number": 1,
            "text": (
                "clc;\nclear all;\nclose all;\n"
                "% Message signal frequency\nfm = 5;\n"
                "% Sampling frequency\nfs = 20;\n"
                "% Continuous time vector for original signal\nt = 0:0.001:1;\n"
                "x = sin(2*pi*fm*t);\n"
                "% Sampling interval Ts = 1/fs\nTs = 1/fs;\nts = 0:Ts:1;\n"
                "xs = sin(2*pi*fm*ts);\n"
                "% Reconstructed signal using interpolation\n"
                "xr = interp1(ts, xs, t, 'spline');\n"
                "subplot(3,1,2);\nstem(ts, xs);\n"
            ),
        },
        {
            "chunk_id": "doc-uuid-1:2:1323-1664",
            "document_id": "doc-uuid-1",
            "filename": "sampling theorem.txt",
            "title": "Sampling Theorem",
            "page_number": 1,
            "text": (
                "% and alternative\nclc;\nclear all;\nclose all;\n"
                "fm = 5;\nfs = 20;\nt = 0:0.001:1;\n"
                "n = 0:1/fs:1;\n"
                "xr = interp1(n, xs, t, 'linear');\n"
            ),
        },
    ]


def test_extract_signal_parameters(sampling_evidence: list[dict[str, str | int | None]]) -> None:
    """Extracts fm, fs, Nyquist rate, Ts, and vector specifications from code."""
    params = extract_signal_parameters(sampling_evidence)

    assert params["fm"] == 5.0
    assert params["fs"] == 20.0
    assert params["nyquist_rate"] == 10.0
    assert params["sampling_interval"] == 0.05
    assert params["is_sufficient"] is True
    assert params["original_time_vector"]["count"] == 1001
    assert params["sampled_time_vector"]["count"] == 21


def test_analyze_math_question_nyquist_rate(
    sampling_evidence: list[dict[str, str | int | None]],
) -> None:
    """Nyquist rate is deterministically calculated as 2 * fm = 10 Hz."""
    params = extract_signal_parameters(sampling_evidence)
    res = analyze_math_question("Calculate the Nyquist rate.", params)

    assert res is not None
    assert res["category"] == "nyquist_rate"
    assert "10 Hz" in res["direct_answer"]
    assert "2 * 5 = 10" in res["direct_answer"]


def test_analyze_math_question_sampling_interval(
    sampling_evidence: list[dict[str, str | int | None]],
) -> None:
    """Sampling interval is deterministically calculated as Ts = 1 / fs = 0.05 s."""
    params = extract_signal_parameters(sampling_evidence)
    res = analyze_math_question("What is the sampling interval?", params)

    assert res is not None
    assert res["category"] == "sampling_interval"
    assert "0.05 seconds" in res["direct_answer"]
    assert "1 / 20 = 0.05" in res["direct_answer"]


def test_analyze_math_question_original_samples(
    sampling_evidence: list[dict[str, str | int | None]],
) -> None:
    """Original samples count is deterministically calculated as 1001 points."""
    params = extract_signal_parameters(sampling_evidence)
    res = analyze_math_question("How many original samples are generated?", params)

    assert res is not None
    assert res["category"] == "original_samples"
    assert "1001" in res["direct_answer"]
    assert "(1.0 - 0.0) / 0.001 + 1 = 1001" in res["explanation"]


def test_analyze_math_question_sampled_points(
    sampling_evidence: list[dict[str, str | int | None]],
) -> None:
    """Sampled points count is deterministically calculated as 21 points."""
    params = extract_signal_parameters(sampling_evidence)
    res = analyze_math_question("How many sampled points are generated?", params)

    assert res is not None
    assert res["category"] == "sampled_points"
    assert "21" in res["direct_answer"]
    assert "21" in res["explanation"]


def test_analyze_math_question_sufficiency(
    sampling_evidence: list[dict[str, str | int | None]],
) -> None:
    """Selected sampling frequency sufficiency check evaluates 20 Hz >= 10 Hz."""
    params = extract_signal_parameters(sampling_evidence)
    res = analyze_math_question("Is the selected sampling frequency sufficient?", params)

    assert res is not None
    assert res["category"] == "sampling_sufficiency"
    assert "sufficient" in res["direct_answer"].lower()
    assert "20 Hz" in res["direct_answer"]
    assert "20 Hz >= 10 Hz" in res["explanation"]


def test_analyze_math_question_8hz_aliasing(
    sampling_evidence: list[dict[str, str | int | None]],
) -> None:
    """Specific frequency evaluation at 8 Hz correctly identifies aliasing."""
    params = extract_signal_parameters(sampling_evidence)
    res = analyze_math_question("What happens at 8 Hz?", params)

    assert res is not None
    assert res["category"] == "frequency_check"
    assert "aliasing occurs" in res["direct_answer"].lower()
    assert "not satisfied" in res["direct_answer"].lower()
    assert "8 Hz < 10 Hz" in res["explanation"]


def test_analyze_math_question_explain_colon_vector(
    sampling_evidence: list[dict[str, str | int | None]],
) -> None:
    """Colon vector explanation provides start, step, end, and 1001 samples."""
    params = extract_signal_parameters(sampling_evidence)
    res = analyze_math_question("Explain t = 0:0.001:1.", params)

    assert res is not None
    assert res["category"] == "vector_explanation"
    assert "1001 points" in res["direct_answer"]
    assert "0.001 seconds" in res["direct_answer"]


def test_analyze_code_identifiers(sampling_evidence: list[dict[str, str | int | None]]) -> None:
    """Identifies MATLAB code commands present in evidence passages."""
    for cmd in ["clc", "clear", "close all", "interp1", "stem"]:
        q = f"What does {cmd} do?"
        res = analyze_code_identifiers(q, sampling_evidence)
        assert res is not None
        assert res["category"] == "code_semantics"
        assert res["command"] == cmd
        assert len(res["direct_answer"]) > 10


def test_validate_model_output_corrects_sample_count_hallucination(
    sampling_evidence: list[dict[str, str | int | None]],
) -> None:
    """BUG-10: When 1B LLM hallucinates '4' for sample count, validation corrects to 1001."""
    params = extract_signal_parameters(sampling_evidence)
    math_res = analyze_math_question("How many original samples are generated?", params)

    # Hallucinated answer emitted by raw Gemma 3 1B
    raw_json = """{
      "answer": "4",
      "direct_answer": "4",
      "archive_context": "t = 0:0.001:1",
      "limitations": [],
      "insufficient_evidence": false,
      "cited_chunk_ids": ["doc-uuid-1:1:485-1321"]
    }"""

    res = validate_model_output(
        raw_json,
        sampling_evidence,
        math_result=math_res,
    )

    assert res["insufficient_evidence"] is False
    assert "1001" in res["direct_answer"]
    assert "1001" in res["answer"]
    assert len(res["citations"]) >= 1
    assert res["citations"][0]["evidence_type"] == "derived"


def test_validate_model_output_corrects_aliasing_hallucination(
    sampling_evidence: list[dict[str, str | int | None]],
) -> None:
    """BUG-10: When 1B LLM claims 'At 8 Hz, the signal is reconstructed', validation corrects."""
    params = extract_signal_parameters(sampling_evidence)
    math_res = analyze_math_question("What happens at 8 Hz?", params)

    # Catastrophic hallucination emitted by raw Gemma 3 1B
    raw_json = """{
      "answer": "At 8 Hz, the signal is reconstructed.",
      "direct_answer": "At 8 Hz, the signal is reconstructed.",
      "archive_context": "Theory",
      "limitations": [],
      "insufficient_evidence": false,
      "cited_chunk_ids": ["doc-uuid-1:0:0-483"]
    }"""

    res = validate_model_output(
        raw_json,
        sampling_evidence,
        math_result=math_res,
    )

    assert res["insufficient_evidence"] is False
    assert "aliasing" in res["direct_answer"].lower()
    assert "not satisfied" in res["direct_answer"].lower()
    assert len(res["citations"]) >= 1
    assert res["citations"][0]["evidence_type"] == "derived"
