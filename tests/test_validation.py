"""Tests for Phase 27: Clinical Validation."""

import math

import pytest

from validation.metrics import (
    sensitivity,
    specificity,
    ppv,
    npv,
    f1_score,
    cohen_kappa,
    fleiss_kappa,
    bland_altman,
    generate_validation_report,
)
from validation.expert_review import ReviewWorkflow


# ── Diagnostic Metrics Tests ─────────────────────────────────


class TestSensitivitySpecificity:
    def test_sensitivity_perfect(self):
        assert sensitivity(100, 0) == 1.0

    def test_sensitivity_zero(self):
        assert sensitivity(0, 100) == 0.0

    def test_sensitivity_known_value(self):
        # TP=80, FN=20 => 80/100 = 0.8
        assert abs(sensitivity(80, 20) - 0.8) < 1e-9

    def test_sensitivity_zero_denom(self):
        assert sensitivity(0, 0) == 0.0

    def test_specificity_perfect(self):
        assert specificity(100, 0) == 1.0

    def test_specificity_zero(self):
        assert specificity(0, 100) == 0.0

    def test_specificity_known_value(self):
        # TN=90, FP=10 => 90/100 = 0.9
        assert abs(specificity(90, 10) - 0.9) < 1e-9

    def test_specificity_zero_denom(self):
        assert specificity(0, 0) == 0.0


class TestPPVNPV:
    def test_ppv_perfect(self):
        assert ppv(100, 0) == 1.0

    def test_ppv_known_value(self):
        # TP=80, FP=20 => 80/100 = 0.8
        assert abs(ppv(80, 20) - 0.8) < 1e-9

    def test_ppv_zero_denom(self):
        assert ppv(0, 0) == 0.0

    def test_npv_perfect(self):
        assert npv(100, 0) == 1.0

    def test_npv_known_value(self):
        # TN=95, FN=5 => 95/100 = 0.95
        assert abs(npv(95, 5) - 0.95) < 1e-9

    def test_npv_zero_denom(self):
        assert npv(0, 0) == 0.0


class TestF1Score:
    def test_f1_perfect(self):
        # TP=100, FP=0, FN=0 => precision=1, recall=1, F1=1
        assert f1_score(100, 0, 0) == 1.0

    def test_f1_known_value(self):
        # TP=80, FP=20, FN=10
        # precision = 80/100 = 0.8, recall = 80/90 = 0.8889
        # F1 = 2 * 0.8 * 0.8889 / (0.8 + 0.8889) = 0.8421
        f1 = f1_score(80, 20, 10)
        assert abs(f1 - 0.8421) < 0.001

    def test_f1_zero(self):
        assert f1_score(0, 0, 0) == 0.0

    def test_f1_no_tp(self):
        assert f1_score(0, 10, 10) == 0.0


# ── Cohen's Kappa Tests ─────────────────────────────────────


class TestCohenKappa:
    def test_perfect_agreement(self):
        # Both raters agree perfectly: 50 positive, 50 negative
        matrix = [[50, 0], [0, 50]]
        kappa = cohen_kappa(matrix)
        assert abs(kappa - 1.0) < 1e-9

    def test_no_agreement_beyond_chance(self):
        # Marginal distributions are equal, agreement equals chance
        matrix = [[25, 25], [25, 25]]
        kappa = cohen_kappa(matrix)
        assert abs(kappa) < 1e-9

    def test_known_kappa_value(self):
        # Example from literature
        # Rater1: 20 yes, 5 no-yes; Rater2: 10 yes-no, 15 no
        matrix = [[20, 5], [10, 15]]
        kappa = cohen_kappa(matrix)
        # po = (20+15)/50 = 0.7
        # pe = (25*30)/(50*50) + (25*20)/(50*50) = 0.3 + 0.2 = 0.5
        # kappa = (0.7 - 0.5)/(1 - 0.5) = 0.4
        assert abs(kappa - 0.4) < 1e-9

    def test_empty_matrix(self):
        assert cohen_kappa([]) == 0.0

    def test_zero_total(self):
        assert cohen_kappa([[0, 0], [0, 0]]) == 0.0


# ── Fleiss' Kappa Tests ──────────────────────────────────────


class TestFleissKappa:
    def test_perfect_agreement(self):
        # 3 raters, 5 subjects, 2 categories, all agree
        ratings = [
            [3, 0],
            [0, 3],
            [3, 0],
            [0, 3],
            [3, 0],
        ]
        kappa = fleiss_kappa(ratings)
        assert abs(kappa - 1.0) < 1e-9

    def test_empty_ratings(self):
        assert fleiss_kappa([]) == 0.0

    def test_single_category(self):
        # All raters always choose category 0
        ratings = [[3, 0], [3, 0], [3, 0]]
        kappa = fleiss_kappa(ratings)
        assert kappa == 1.0  # pe = 1.0, function returns 1.0


# ── Bland-Altman Tests ───────────────────────────────────────


class TestBlandAltman:
    def test_identical_values(self):
        measured = [10.0, 20.0, 30.0, 40.0, 50.0]
        reference = [10.0, 20.0, 30.0, 40.0, 50.0]
        ba = bland_altman(measured, reference)
        assert ba["mean_diff"] == 0.0
        assert ba["std_diff"] == 0.0
        assert ba["upper_loa"] == 0.0
        assert ba["lower_loa"] == 0.0
        assert ba["n"] == 5

    def test_constant_bias(self):
        measured = [11.0, 21.0, 31.0, 41.0, 51.0]
        reference = [10.0, 20.0, 30.0, 40.0, 50.0]
        ba = bland_altman(measured, reference)
        assert abs(ba["mean_diff"] - 1.0) < 1e-9
        assert abs(ba["std_diff"]) < 1e-9

    def test_known_values(self):
        measured = [10.0, 20.0, 30.0]
        reference = [12.0, 18.0, 32.0]
        ba = bland_altman(measured, reference)
        # Differences: -2, 2, -2 => mean = -0.6667
        diffs = [-2.0, 2.0, -2.0]
        mean_d = sum(diffs) / 3
        assert abs(ba["mean_diff"] - mean_d) < 1e-4
        assert ba["n"] == 3

    def test_empty_inputs(self):
        ba = bland_altman([], [])
        assert ba["n"] == 0
        assert ba["mean_diff"] == 0.0

    def test_mismatched_lengths(self):
        with pytest.raises(ValueError):
            bland_altman([1.0, 2.0], [1.0])

    def test_loa_symmetric_for_zero_bias(self):
        measured = [10.0, 20.0, 30.0, 40.0, 50.0]
        reference = [10.0, 20.0, 30.0, 40.0, 50.0]
        ba = bland_altman(measured, reference)
        assert ba["upper_loa"] == -ba["lower_loa"]


# ── Validation Report Tests ──────────────────────────────────


class TestValidationReport:
    def test_generate_report_basic(self):
        results = {"tp": 80, "fp": 10, "fn": 20, "tn": 90}
        report = generate_validation_report(results)
        assert "CLINICAL VALIDATION REPORT" in report
        assert "Sensitivity" in report
        assert "Specificity" in report
        assert "F1 Score" in report

    def test_generate_report_with_bland_altman(self):
        results = {
            "tp": 80, "fp": 10, "fn": 20, "tn": 90,
            "measured": [10.0, 20.0, 30.0],
            "reference": [10.0, 20.0, 30.0],
        }
        report = generate_validation_report(results)
        assert "Bland-Altman" in report

    def test_generate_report_with_kappa(self):
        results = {
            "tp": 80, "fp": 10, "fn": 20, "tn": 90,
            "kappa_matrix": [[50, 0], [0, 50]],
        }
        report = generate_validation_report(results)
        assert "Cohen's Kappa" in report
        assert "Almost perfect" in report


# ── Expert Review Workflow Tests ─────────────────────────────


class TestReviewWorkflow:
    def test_create_review_task(self, sample_report):
        wf = ReviewWorkflow()
        task = wf.create_review_task(sample_report, "/path/to/ecg.png")
        assert "task_id" in task
        assert task["status"] == "pending"
        assert task["reviews_count"] == 0

    def test_submit_review(self, sample_report):
        wf = ReviewWorkflow()
        task = wf.create_review_task(sample_report, "/path/to/ecg.png")
        review = {
            "findings": ["Normal sinus rhythm"],
            "measurements_correct": True,
            "interpretation_correct": True,
            "flags_correct": True,
            "overall_rating": 4,
            "comments": "Good analysis",
            "diagnoses": ["Normal ECG"],
        }
        result = wf.submit_review(task["task_id"], "expert-1", review)
        assert "review_id" in result
        assert result["expert_id"] == "expert-1"

    def test_submit_review_invalid_task(self):
        wf = ReviewWorkflow()
        with pytest.raises(ValueError):
            wf.submit_review("nonexistent", "expert-1", {})

    def test_task_status_updates(self, sample_report):
        wf = ReviewWorkflow()
        task = wf.create_review_task(sample_report, "/path/to/ecg.png")
        tid = task["task_id"]
        review = {"measurements_correct": True, "interpretation_correct": True, "flags_correct": True}
        wf.submit_review(tid, "expert-1", review)
        assert wf._tasks[tid]["status"] == "pending"
        wf.submit_review(tid, "expert-2", review)
        assert wf._tasks[tid]["status"] == "reviewed"


class TestGoldStandard:
    def test_majority_vote_agreement(self):
        wf = ReviewWorkflow()
        reviews = [
            {"measurements_correct": True, "interpretation_correct": True, "flags_correct": True,
             "diagnoses": ["Normal"], "overall_rating": 4},
            {"measurements_correct": True, "interpretation_correct": True, "flags_correct": True,
             "diagnoses": ["Normal"], "overall_rating": 5},
            {"measurements_correct": True, "interpretation_correct": False, "flags_correct": True,
             "diagnoses": ["Normal", "Bradycardia"], "overall_rating": 3},
        ]
        gs = wf.get_gold_standard(reviews, method="majority")
        assert gs["method"] == "majority"
        assert gs["gold_standard"]["measurements_correct"] is True
        assert gs["gold_standard"]["flags_correct"] is True
        assert "Normal" in gs["gold_standard"]["diagnoses"]
        assert gs["confidence"] == "high"

    def test_single_reviewer(self):
        wf = ReviewWorkflow()
        reviews = [{"measurements_correct": True, "overall_rating": 5}]
        gs = wf.get_gold_standard(reviews)
        assert gs["confidence"] == "low"

    def test_empty_reviews(self):
        wf = ReviewWorkflow()
        gs = wf.get_gold_standard([])
        assert "error" in gs

    def test_consensus_method(self):
        wf = ReviewWorkflow()
        reviews = [
            {"measurements_correct": True, "interpretation_correct": True, "flags_correct": True},
            {"measurements_correct": True, "interpretation_correct": False, "flags_correct": True},
        ]
        gs = wf.get_gold_standard(reviews, method="consensus")
        gold = gs["gold_standard"]
        # measurements_correct: both True -> True
        assert gold["measurements_correct"] is True
        # interpretation_correct: disagree -> None (uncertain)
        assert gold["interpretation_correct"] is None
        # flags_correct: both True -> True
        assert gold["flags_correct"] is True
