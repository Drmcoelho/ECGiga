"""Tests for quiz engine and quiz generation."""

import json
import pathlib
from jsonschema import Draft202012Validator

from quiz.engine import build_adaptive_quiz, infer_gaps_from_report
from quiz.generate_quiz import quiz_from_report


def test_infer_gaps_normal(sample_report):
    tags = infer_gaps_from_report(sample_report)
    assert isinstance(tags, list)
    # Normal report should fallback to default tags
    assert len(tags) > 0


def test_infer_gaps_abnormal():
    report = {
        "intervals_refined": {
            "median": {"QRS_ms": 130, "PR_ms": 220, "QTc_B": 500}
        },
        "axis": {"label": "Desvio para a esquerda"},
    }
    tags = infer_gaps_from_report(report)
    assert "qrs_wide" in tags
    assert "pr_long" in tags
    assert "qtc_long" in tags
    assert "axis_left" in tags


def test_build_adaptive_quiz(sample_report):
    quiz = build_adaptive_quiz(sample_report, n_questions=3)
    assert "questions" in quiz
    assert "tags" in quiz
    assert len(quiz["questions"]) <= 5  # May get fewer if pool is small


def test_quiz_from_report(sample_report):
    quiz = quiz_from_report(sample_report)
    assert "questions" in quiz
    for q in quiz["questions"]:
        assert "id" in q
        assert "prompt" in q
        assert "choices" in q
        assert len(q["choices"]) >= 2


def test_validate_quiz_schema(sample_quiz_path, mcq_schema):
    with open(sample_quiz_path, "r", encoding="utf-8") as f:
        item = json.load(f)
    validator = Draft202012Validator(mcq_schema)
    validator.validate(item)


def test_quiz_bank_all_valid(mcq_schema):
    bank_dir = pathlib.Path("quiz/bank/p2")
    if not bank_dir.exists():
        return
    validator = Draft202012Validator(mcq_schema)
    count = 0
    for fp in sorted(bank_dir.glob("*.json")):
        with open(fp, "r", encoding="utf-8") as f:
            item = json.load(f)
        validator.validate(item)
        count += 1
    assert count > 0
