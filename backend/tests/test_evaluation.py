"""Deterministic evaluation runner tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.evaluation.runner import EvaluationConfig, evaluate

ROOT = Path(__file__).resolve().parents[2]


def test_evaluation_covers_all_categories_and_reports_metrics() -> None:
    result = evaluate(
        EvaluationConfig(
            ROOT / "data" / "evaluation" / "questions.json",
            ROOT / "data" / "sample_archive",
        )
    )

    assert result["dataset_size"] == 20
    assert result["category_count"] == 8
    assert result["answerable_questions"] == 15
    assert result["unanswerable_questions"] == 5
    assert result["metrics"]["expected_source_file_coverage"] == 1
    assert result["metrics"]["expected_answer_phrase_coverage"] == 1
    assert 0 <= result["metrics"]["lexical_source_hit_at_5"] <= 1


def test_evaluation_rejects_missing_category(tmp_path: Path) -> None:
    questions = ROOT / "data" / "evaluation" / "questions.json"
    payload = questions.read_text(encoding="utf-8").replace(
        '"category": "contradiction"', '"category": "answerable_factual"'
    )
    questions_path = tmp_path / "questions.json"
    questions_path.write_text(payload, encoding="utf-8")

    with pytest.raises(ValueError, match="missing categories"):
        evaluate(EvaluationConfig(questions_path, ROOT / "data" / "sample_archive"))
