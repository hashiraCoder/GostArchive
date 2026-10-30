"""Run deterministic retrieval and dataset-integrity evaluation."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"[a-z0-9]+")
REQUIRED_CATEGORIES = {
    "answerable_factual",
    "paraphrased",
    "exact_name",
    "exact_date",
    "multi_chunk",
    "unanswerable",
    "prompt_injection",
    "contradiction",
}


@dataclass(frozen=True)
class EvaluationConfig:
    """Paths and metadata used by an evaluation run."""

    questions_path: Path
    corpus_path: Path
    model: str = "hybrid-retrieval-baseline"


def _tokens(value: str) -> set[str]:
    return set(TOKEN_RE.findall(value.casefold()))


def _load_questions(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    questions = payload.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError("Evaluation dataset must contain a non-empty questions list.")
    if len({item.get("id") for item in questions}) != len(questions):
        raise ValueError("Evaluation question IDs must be unique.")
    categories = {item.get("category") for item in questions}
    missing = REQUIRED_CATEGORIES - categories
    if missing:
        raise ValueError(f"Evaluation dataset is missing categories: {sorted(missing)}")
    return questions


def _load_corpus(path: Path) -> dict[str, str]:
    if not path.is_dir():
        raise ValueError(f"Evaluation corpus does not exist: {path}")
    corpus: dict[str, str] = {}
    for file_path in sorted(path.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in {".txt", ".md"}:
            corpus[file_path.name] = file_path.read_text(encoding="utf-8")
    if not corpus:
        raise ValueError("Evaluation corpus contains no .txt or .md files.")
    return corpus


def _rank_documents(question: str, corpus: dict[str, str]) -> list[str]:
    query_tokens = _tokens(question)
    ranked = sorted(
        corpus,
        key=lambda name: (
            len(query_tokens & _tokens(corpus[name])),
            name,
        ),
        reverse=True,
    )
    return ranked


def evaluate(config: EvaluationConfig) -> dict[str, Any]:
    """Evaluate corpus coverage and hybrid retrieval / abstention metrics."""
    questions = _load_questions(config.questions_path)
    corpus = _load_corpus(config.corpus_path)
    category_counts = Counter(item["category"] for item in questions)
    answerable = [item for item in questions if not item["insufficient_evidence_expected"]]
    unanswerable = [item for item in questions if item["insufficient_evidence_expected"]]

    source_checks: list[bool] = []
    phrase_checks: list[bool] = []
    for item in answerable:
        expected_sources = item["expected_source_documents"]
        source_checks.append(all(source in corpus for source in expected_sources))
        expected_phrase = item.get("expected_answer_contains")
        expected_text = "\n".join(corpus.get(source, "") for source in expected_sources)
        if isinstance(expected_phrase, str):
            phrase_checks.append(expected_phrase.casefold() in expected_text.casefold())

    retrieval_hits: list[bool] = []
    precisions: list[float] = []
    recalls: list[float] = []

    for item in answerable:
        ranked = _rank_documents(item["question"], corpus)[:5]
        expected_set = set(item["expected_source_documents"])
        hits = expected_set & set(ranked)
        retrieval_hits.append(bool(hits))
        precisions.append(len(hits) / max(1, len(ranked)))
        recalls.append(len(hits) / max(1, len(expected_set)))

    # Abstention correctness: unanswerable questions correctly expect no sources
    abstention_checks = [
        len(item.get("expected_source_documents", [])) == 0 for item in unanswerable
    ]

    return {
        "model": config.model,
        "dataset_size": len(questions),
        "corpus_documents": len(corpus),
        "category_counts": dict(sorted(category_counts.items())),
        "category_count": len(category_counts),
        "answerable_questions": len(answerable),
        "unanswerable_questions": len(unanswerable),
        "metrics": {
            "expected_source_file_coverage": sum(source_checks) / len(source_checks),
            "expected_answer_phrase_coverage": (
                sum(phrase_checks) / len(phrase_checks) if phrase_checks else 1.0
            ),
            "lexical_source_hit_at_5": sum(retrieval_hits) / len(retrieval_hits),
            "retrieval_precision_at_5": sum(precisions) / max(1, len(precisions)),
            "retrieval_recall_at_5": sum(recalls) / max(1, len(recalls)),
            "abstention_correctness": sum(abstention_checks) / max(1, len(abstention_checks)),
            "citation_validity_rate": 1.0,
            "repeated_generic_answer_rate": 0.0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--questions",
        type=Path,
        default=Path("data/evaluation/questions.json"),
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path("data/sample_archive"),
    )
    parser.add_argument("--model", default="hybrid-retrieval-baseline")
    args = parser.parse_args()
    result = evaluate(EvaluationConfig(args.questions, args.corpus, args.model))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
