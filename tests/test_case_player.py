"""Tests for the case_player package (generator + scorer)."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from case_player.generator import (
    case_to_html,
    generate_case,
    generate_case_index,
)
from case_player.scorer import (
    calculate_iou,
    generate_feedback,
    score_annotations,
)

# ------------------------------------------------------------------ #
#  Fixtures                                                           #
# ------------------------------------------------------------------ #

@pytest.fixture()
def sample_report():
    return {
        "diagnosis": "Ritmo sinusal normal",
        "clinical_history": "Paciente masculino, 45 anos, assintomatico.",
        "rhythm": "sinus",
        "rate": 72,
        "axis": "normal",
        "p_wave": "Presente em todas as derivacoes",
        "qrs_complex": "Estreito, duracao normal",
        "st_segment": "Isoeletrico",
        "t_wave": "Positiva nas derivacoes esperadas",
        "intervals": {"pr_ms": 160, "qrs_ms": 88, "qt_ms": 380, "qtc_ms": 410},
    }


@pytest.fixture()
def sample_case(sample_report):
    return generate_case(sample_report, image_path="/img/ecg01.png", difficulty="medium")


# ------------------------------------------------------------------ #
#  generate_case                                                      #
# ------------------------------------------------------------------ #

class TestGenerateCase:
    def test_produces_valid_structure(self, sample_case):
        required_keys = {
            "id", "title", "description", "image_url",
            "report", "annotations", "questions", "answer_key", "difficulty",
        }
        assert required_keys.issubset(sample_case.keys())

    def test_id_is_string(self, sample_case):
        assert isinstance(sample_case["id"], str)
        assert len(sample_case["id"]) == 12

    def test_title_from_diagnosis(self, sample_report):
        case = generate_case(sample_report)
        assert case["title"] == "Ritmo sinusal normal"

    def test_image_url_preserved(self, sample_case):
        assert sample_case["image_url"] == "/img/ecg01.png"

    def test_difficulty_values(self, sample_report):
        for d in ("easy", "medium", "hard"):
            c = generate_case(sample_report, difficulty=d)
            assert c["difficulty"] == d

    def test_invalid_difficulty_raises(self, sample_report):
        with pytest.raises(ValueError, match="difficulty"):
            generate_case(sample_report, difficulty="extreme")

    def test_annotations_extracted_from_report(self, sample_case):
        labels = [a["label"] for a in sample_case["annotations"]]
        assert "p_wave" in labels
        assert "qrs_complex" in labels

    def test_questions_populated(self, sample_case):
        assert len(sample_case["questions"]) > 0

    def test_deterministic_id(self, sample_report):
        a = generate_case(sample_report)
        b = generate_case(sample_report)
        assert a["id"] == b["id"]


# ------------------------------------------------------------------ #
#  generate_case_index                                                #
# ------------------------------------------------------------------ #

class TestGenerateCaseIndex:
    def test_writes_index_json(self, sample_case):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = generate_case_index([sample_case], tmpdir)
            assert os.path.isfile(path)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            assert data["count"] == 1
            assert data["cases"][0]["id"] == sample_case["id"]

    def test_writes_to_explicit_file(self, sample_case):
        with tempfile.TemporaryDirectory() as tmpdir:
            fp = os.path.join(tmpdir, "my_index.json")
            path = generate_case_index([sample_case], fp)
            assert path.endswith("my_index.json")
            assert os.path.isfile(path)


# ------------------------------------------------------------------ #
#  calculate_iou                                                      #
# ------------------------------------------------------------------ #

class TestCalculateIoU:
    def test_perfect_overlap(self):
        box = {"x": 0, "y": 0, "w": 10, "h": 10}
        assert calculate_iou([box], [box]) == pytest.approx(1.0)

    def test_no_overlap(self):
        a = {"x": 0, "y": 0, "w": 10, "h": 10}
        b = {"x": 20, "y": 20, "w": 10, "h": 10}
        assert calculate_iou([a], [b]) == pytest.approx(0.0)

    def test_partial_overlap(self):
        a = {"x": 0, "y": 0, "w": 10, "h": 10}
        b = {"x": 5, "y": 5, "w": 10, "h": 10}
        # Intersection: 5x5=25, Union: 100+100-25=175
        assert calculate_iou([a], [b]) == pytest.approx(25 / 175)

    def test_empty_pred(self):
        gt = {"x": 0, "y": 0, "w": 10, "h": 10}
        assert calculate_iou([], [gt]) == 0.0

    def test_empty_gt(self):
        pred = {"x": 0, "y": 0, "w": 10, "h": 10}
        assert calculate_iou([pred], []) == 0.0

    def test_multiple_boxes(self):
        gt1 = {"x": 0, "y": 0, "w": 10, "h": 10}
        gt2 = {"x": 50, "y": 50, "w": 10, "h": 10}
        # Perfect pred for both
        iou = calculate_iou([gt1, gt2], [gt1, gt2])
        assert iou == pytest.approx(1.0)

    def test_known_iou_value(self):
        a = {"x": 0, "y": 0, "w": 20, "h": 20}
        b = {"x": 10, "y": 0, "w": 20, "h": 20}
        # Intersection: 10x20=200, Union: 400+400-200=600
        assert calculate_iou([a], [b]) == pytest.approx(200 / 600)


# ------------------------------------------------------------------ #
#  score_annotations                                                  #
# ------------------------------------------------------------------ #

class TestScoreAnnotations:
    def test_perfect_match(self):
        box = {"x": 0, "y": 0, "w": 10, "h": 10}
        key = {"P_wave": [box]}
        student = {"P_wave": [box]}
        result = score_annotations(student, key)
        assert result["total_score"] == pytest.approx(1.0)
        assert result["tp"] == 1
        assert result["fp"] == 0
        assert result["fn"] == 0
        assert result["macro_f1"] == pytest.approx(1.0)

    def test_partial_match(self):
        gt = {"x": 0, "y": 0, "w": 10, "h": 10}
        pred_good = {"x": 1, "y": 1, "w": 10, "h": 10}  # high IoU
        pred_bad = {"x": 100, "y": 100, "w": 10, "h": 10}  # no overlap
        key = {"P_wave": [gt]}
        student = {"P_wave": [pred_good, pred_bad]}
        result = score_annotations(student, key)
        assert result["tp"] == 1
        assert result["fp"] == 1
        assert result["fn"] == 0
        assert 0 < result["macro_f1"] < 1.0

    def test_all_misses(self):
        gt = {"x": 0, "y": 0, "w": 10, "h": 10}
        pred = {"x": 200, "y": 200, "w": 10, "h": 10}
        result = score_annotations({"P_wave": [pred]}, {"P_wave": [gt]})
        assert result["tp"] == 0
        assert result["fp"] == 1
        assert result["fn"] == 1
        assert result["total_score"] == pytest.approx(0.0)

    def test_extra_label(self):
        gt = {"x": 0, "y": 0, "w": 10, "h": 10}
        result = score_annotations(
            {"P_wave": [gt], "QRS": [gt]},
            {"P_wave": [gt]},
        )
        # P_wave is perfect, QRS is entirely FP
        assert result["tp"] == 1
        assert result["fp"] == 1
        assert result["fn"] == 0

    def test_missing_label(self):
        gt = {"x": 0, "y": 0, "w": 10, "h": 10}
        result = score_annotations(
            {},
            {"P_wave": [gt]},
        )
        assert result["tp"] == 0
        assert result["fn"] == 1

    def test_per_label_scores_present(self):
        gt = {"x": 0, "y": 0, "w": 10, "h": 10}
        result = score_annotations({"P_wave": [gt]}, {"P_wave": [gt]})
        assert "P_wave" in result["per_label_scores"]
        plabel = result["per_label_scores"]["P_wave"]
        assert plabel["precision"] == pytest.approx(1.0)
        assert plabel["recall"] == pytest.approx(1.0)
        assert plabel["f1"] == pytest.approx(1.0)


# ------------------------------------------------------------------ #
#  case_to_html                                                       #
# ------------------------------------------------------------------ #

class TestCaseToHtml:
    def test_produces_valid_html(self, sample_case):
        html = case_to_html(sample_case)
        assert isinstance(html, str)
        assert html.strip().startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_contains_title(self, sample_case):
        html = case_to_html(sample_case)
        assert sample_case["title"] in html

    def test_contains_image_tag(self, sample_case):
        html = case_to_html(sample_case)
        assert "ecg-img" in html
        assert sample_case["image_url"] in html

    def test_no_image_when_empty(self, sample_report):
        case = generate_case(sample_report, image_path=None)
        html = case_to_html(case)
        assert "<img" not in html


# ------------------------------------------------------------------ #
#  generate_feedback                                                  #
# ------------------------------------------------------------------ #

class TestGenerateFeedback:
    def test_produces_text(self):
        score = {
            "total_score": 0.8,
            "macro_f1": 0.75,
            "tp": 3,
            "fp": 1,
            "fn": 1,
            "per_label_scores": {
                "P_wave": {"tp": 2, "fp": 0, "fn": 0, "precision": 1.0, "recall": 1.0, "f1": 1.0},
                "QRS": {"tp": 1, "fp": 1, "fn": 1, "precision": 0.5, "recall": 0.5, "f1": 0.5},
            },
        }
        text = generate_feedback(score)
        assert isinstance(text, str)
        assert len(text) > 0
        # Should contain Portuguese content
        assert "Pontuacao" in text or "geral" in text

    def test_perfect_score_feedback(self):
        score = {
            "total_score": 1.0,
            "macro_f1": 1.0,
            "tp": 5,
            "fp": 0,
            "fn": 0,
            "per_label_scores": {},
        }
        text = generate_feedback(score)
        assert "Excelente" in text

    def test_low_score_feedback(self):
        score = {
            "total_score": 0.2,
            "macro_f1": 0.15,
            "tp": 1,
            "fp": 5,
            "fn": 4,
            "per_label_scores": {},
        }
        text = generate_feedback(score)
        assert "abaixo" in text

    def test_zero_tp_feedback(self):
        score = {
            "total_score": 0.0,
            "macro_f1": 0.0,
            "tp": 0,
            "fp": 3,
            "fn": 2,
            "per_label_scores": {},
        }
        text = generate_feedback(score)
        assert "Nenhuma anotacao" in text

    def test_contains_f1_info(self):
        score = {
            "total_score": 0.6,
            "macro_f1": 0.55,
            "tp": 3,
            "fp": 2,
            "fn": 2,
            "per_label_scores": {},
        }
        text = generate_feedback(score)
        assert "F1 macro" in text
