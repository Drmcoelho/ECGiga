"""Tests for content modules (ECG basics and intermediate)."""

import json
from pathlib import Path
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_ecg_basics_manifest_exists():
    manifest = REPO_ROOT / "content" / "modules" / "ecg-basics" / "manifest.yaml"
    assert manifest.exists(), "ECG basics manifest.yaml not found"


def test_ecg_basics_lessons_exist():
    lessons_dir = REPO_ROOT / "content" / "modules" / "ecg-basics" / "lessons"
    assert lessons_dir.exists()
    md_files = list(lessons_dir.glob("*.md"))
    assert len(md_files) >= 5, f"Expected at least 5 lessons, found {len(md_files)}"


def test_ecg_basics_quiz_valid():
    quiz_dir = REPO_ROOT / "content" / "modules" / "ecg-basics" / "quizzes"
    json_files = list(quiz_dir.glob("*.json"))
    assert len(json_files) >= 1

    for f in json_files:
        data = json.loads(f.read_text(encoding="utf-8"))
        # Support both {"questions": [...]} and bare list formats
        if isinstance(data, list):
            questions = data
        elif isinstance(data, dict):
            questions = data.get("questions", [])
        else:
            questions = []
        assert len(questions) >= 5, f"{f.name} has too few questions"
        for q in questions:
            assert "id" in q
            assert "stem" in q
            assert "options" in q


def test_ecg_basics_case_valid():
    cases_dir = REPO_ROOT / "content" / "modules" / "ecg-basics" / "cases"
    json_files = list(cases_dir.glob("*.json"))
    assert len(json_files) >= 1

    for f in json_files:
        case = json.loads(f.read_text(encoding="utf-8"))
        assert "id" in case, f"{f.name} missing id"
        assert "phases" in case, f"{f.name} missing phases"
        assert len(case["phases"]) >= 3, f"{f.name} has too few phases"


def test_ecg_intermediate_manifest_exists():
    manifest = REPO_ROOT / "content" / "modules" / "ecg-intermediate" / "manifest.yaml"
    assert manifest.exists(), "ECG intermediate manifest.yaml not found"


def test_ecg_intermediate_cases_exist():
    cases_dir = REPO_ROOT / "content" / "modules" / "ecg-intermediate" / "cases"
    assert cases_dir.exists()
    json_files = list(cases_dir.glob("*.json"))
    assert len(json_files) >= 4, f"Expected at least 4 cases, found {len(json_files)}"


def test_ecg_intermediate_cases_valid():
    cases_dir = REPO_ROOT / "content" / "modules" / "ecg-intermediate" / "cases"
    for f in cases_dir.glob("*.json"):
        case = json.loads(f.read_text(encoding="utf-8"))
        assert "id" in case, f"{f.name} missing id"
        assert "phases" in case, f"{f.name} missing phases"
        assert len(case["phases"]) >= 3, f"{f.name} has too few phases"
        for phase in case["phases"]:
            # Support both formats: step/instruction/expected and question/answer
            has_structured = "step" in phase and "instruction" in phase
            has_qa = "question" in phase and "answer" in phase
            assert has_structured or has_qa, f"{f.name} phase missing required keys"
