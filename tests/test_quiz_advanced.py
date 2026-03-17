"""Tests for Phase 26: Gamified Quiz (spaced repetition, adaptive, progress)."""

import json
import pathlib
from datetime import datetime, timedelta

import pytest

from quiz.spaced_repetition import SpacedRepetitionScheduler, QuestionState
from quiz.adaptive import AdaptiveEngine
from quiz.progress import ProgressTracker, BADGES


# ── SpacedRepetitionScheduler Tests ──────────────────────────


class TestQuestionState:
    def test_default_values(self):
        qs = QuestionState()
        assert qs.ease_factor == 2.5
        assert qs.interval == 1
        assert qs.repetitions == 0
        assert qs.next_review != ""

    def test_to_dict_roundtrip(self):
        qs = QuestionState(ease_factor=2.0, interval=3, repetitions=2)
        d = qs.to_dict()
        qs2 = QuestionState.from_dict(d)
        assert qs2.ease_factor == qs.ease_factor
        assert qs2.interval == qs.interval
        assert qs2.repetitions == qs.repetitions


class TestSpacedRepetitionScheduler:
    def test_init_creates_empty_state(self, tmp_path):
        path = str(tmp_path / "sr_test.json")
        srs = SpacedRepetitionScheduler(data_path=path)
        assert srs.get_stats()["total_questions"] == 0

    def test_record_correct_answer(self, tmp_path):
        path = str(tmp_path / "sr_test.json")
        srs = SpacedRepetitionScheduler(data_path=path)
        srs.record_answer("q1", quality=4)
        stats = srs.get_stats()
        assert stats["total_questions"] == 1
        assert stats["total_reviews"] == 1

    def test_record_incorrect_answer_resets(self, tmp_path):
        path = str(tmp_path / "sr_test.json")
        srs = SpacedRepetitionScheduler(data_path=path)
        # First: correct
        srs.record_answer("q1", quality=5)
        srs.record_answer("q1", quality=5)
        # Then: fail
        srs.record_answer("q1", quality=1)
        # Interval should reset
        assert srs._states["q1"].repetitions == 0
        assert srs._states["q1"].interval == 1

    def test_ease_factor_adjusts(self, tmp_path):
        path = str(tmp_path / "sr_test.json")
        srs = SpacedRepetitionScheduler(data_path=path)
        srs.record_answer("q1", quality=5)
        ef_after_5 = srs._states["q1"].ease_factor
        assert ef_after_5 > 2.5  # Should increase for quality=5

    def test_ease_factor_minimum(self, tmp_path):
        path = str(tmp_path / "sr_test.json")
        srs = SpacedRepetitionScheduler(data_path=path)
        # Many poor answers
        for _ in range(20):
            srs.record_answer("q1", quality=0)
        assert srs._states["q1"].ease_factor >= 1.3

    def test_save_and_load(self, tmp_path):
        path = str(tmp_path / "sr_test.json")
        srs = SpacedRepetitionScheduler(data_path=path)
        srs.record_answer("q1", quality=4)
        srs.record_answer("q2", quality=3)

        # Load in new instance
        srs2 = SpacedRepetitionScheduler(data_path=path)
        assert srs2.get_stats()["total_questions"] == 2

    def test_get_due_questions(self, tmp_path):
        path = str(tmp_path / "sr_test.json")
        srs = SpacedRepetitionScheduler(data_path=path)
        # Record answers - they should be due today after a fail
        srs.record_answer("q1", quality=0)
        srs.record_answer("q2", quality=0)
        # Force next_review to today
        today = datetime.now().strftime("%Y-%m-%d")
        srs._states["q1"].next_review = today
        srs._states["q2"].next_review = today
        due = srs.get_due_questions(n=10)
        assert "q1" in due
        assert "q2" in due

    def test_get_stats_with_data(self, tmp_path):
        path = str(tmp_path / "sr_test.json")
        srs = SpacedRepetitionScheduler(data_path=path)
        srs.record_answer("q1", quality=5)
        srs.record_answer("q1", quality=5)
        srs.record_answer("q1", quality=5)
        srs.record_answer("q2", quality=2)
        stats = srs.get_stats()
        assert stats["total_questions"] == 2
        assert stats["total_reviews"] == 4
        assert stats["accuracy"] > 0


# ── AdaptiveEngine Tests ─────────────────────────────────────


class TestAdaptiveEngine:
    def test_init(self):
        engine = AdaptiveEngine(quiz_bank_path="quiz/bank")
        # Should not crash even if bank has questions
        assert engine is not None

    def test_estimate_ability_empty_history(self):
        engine = AdaptiveEngine(quiz_bank_path="nonexistent_path")
        ability = engine.estimate_ability([])
        assert ability == 0.5

    def test_estimate_ability_all_correct(self):
        engine = AdaptiveEngine(quiz_bank_path="nonexistent_path")
        history = [{"question_id": f"q{i}", "correct": True, "tag": "test"} for i in range(20)]
        ability = engine.estimate_ability(history)
        assert ability > 0.7

    def test_estimate_ability_all_wrong(self):
        engine = AdaptiveEngine(quiz_bank_path="nonexistent_path")
        history = [{"question_id": f"q{i}", "correct": False, "tag": "test"} for i in range(20)]
        ability = engine.estimate_ability(history)
        assert ability < 0.3

    def test_estimate_ability_mixed(self):
        engine = AdaptiveEngine(quiz_bank_path="nonexistent_path")
        history = [
            {"question_id": f"q{i}", "correct": i % 2 == 0, "tag": "test"}
            for i in range(20)
        ]
        ability = engine.estimate_ability(history)
        assert 0.3 < ability < 0.7

    def test_recommend_topics_weak(self):
        engine = AdaptiveEngine(quiz_bank_path="nonexistent_path")
        history = [
            {"question_id": "q1", "correct": False, "tag": "axis"},
            {"question_id": "q2", "correct": False, "tag": "axis"},
            {"question_id": "q3", "correct": False, "tag": "axis"},
            {"question_id": "q4", "correct": True, "tag": "rhythm"},
            {"question_id": "q5", "correct": True, "tag": "rhythm"},
            {"question_id": "q6", "correct": True, "tag": "rhythm"},
        ]
        weak = engine.recommend_topics(history)
        assert "axis" in weak
        assert "rhythm" not in weak

    def test_select_next_question_from_bank(self):
        engine = AdaptiveEngine(quiz_bank_path="quiz/bank")
        if not engine._questions:
            pytest.skip("No questions in quiz bank")
        history = []
        q = engine.select_next_question(history)
        assert isinstance(q, dict)
        assert "id" in q or "prompt" in q

    def test_generate_progress_report(self):
        engine = AdaptiveEngine(quiz_bank_path="nonexistent_path")
        history = [
            {"question_id": f"q{i}", "correct": i % 3 != 0, "tag": "axis" if i < 5 else "rhythm"}
            for i in range(20)
        ]
        report = engine.generate_progress_report(history)
        assert "ability" in report
        assert "total_questions" in report
        assert "overall_accuracy" in report
        assert "topic_breakdown" in report
        assert "strong_topics" in report
        assert "weak_topics" in report
        assert "recommendations" in report


# ── ProgressTracker Tests ────────────────────────────────────


class TestProgressTracker:
    def test_init_creates_dir(self, tmp_path):
        data_dir = str(tmp_path / "progress_test")
        ProgressTracker(data_dir=data_dir)
        assert pathlib.Path(data_dir).exists()

    def test_record_session(self, tmp_path):
        pt = ProgressTracker(data_dir=str(tmp_path / "progress"))
        results = [
            {"question_id": "q1", "correct": True, "tag": "axis"},
            {"question_id": "q2", "correct": False, "tag": "rhythm"},
        ]
        pt.record_session(results)
        history = pt.get_history()
        assert len(history) == 2

    def test_get_history_filtered(self, tmp_path):
        pt = ProgressTracker(data_dir=str(tmp_path / "progress"))
        results = [
            {"question_id": "q1", "correct": True, "tag": "axis"},
            {"question_id": "q2", "correct": False, "tag": "rhythm"},
        ]
        pt.record_session(results)
        axis_history = pt.get_history(topic="axis")
        assert len(axis_history) == 1
        assert axis_history[0]["tag"] == "axis"

    def test_get_streak_no_sessions(self, tmp_path):
        pt = ProgressTracker(data_dir=str(tmp_path / "progress"))
        assert pt.get_streak() == 0

    def test_get_streak_with_today(self, tmp_path):
        pt = ProgressTracker(data_dir=str(tmp_path / "progress"))
        # Record a session (will have today's date)
        pt.record_session([{"question_id": "q1", "correct": True}])
        assert pt.get_streak() >= 1

    def test_badges_first_quiz(self, tmp_path):
        pt = ProgressTracker(data_dir=str(tmp_path / "progress"))
        pt.record_session([{"question_id": "q1", "correct": True}])
        badges = pt.get_badges()
        first_quiz = next(b for b in badges if b["id"] == "first_quiz")
        assert first_quiz["earned"] is True

    def test_badges_no_quiz(self, tmp_path):
        pt = ProgressTracker(data_dir=str(tmp_path / "progress"))
        badges = pt.get_badges()
        first_quiz = next(b for b in badges if b["id"] == "first_quiz")
        assert first_quiz["earned"] is False

    def test_badges_perfect_10(self, tmp_path):
        pt = ProgressTracker(data_dir=str(tmp_path / "progress"))
        # Record 10+ correct in a row
        results = [{"question_id": f"q{i}", "correct": True} for i in range(12)]
        pt.record_session(results)
        badges = pt.get_badges()
        perfect = next(b for b in badges if b["id"] == "perfect_10")
        assert perfect["earned"] is True

    def test_get_dashboard_data(self, tmp_path):
        pt = ProgressTracker(data_dir=str(tmp_path / "progress"))
        pt.record_session([
            {"question_id": "q1", "correct": True, "tag": "axis"},
            {"question_id": "q2", "correct": False, "tag": "rhythm"},
        ])
        dashboard = pt.get_dashboard_data()
        assert dashboard["total_questions_answered"] == 2
        assert dashboard["total_correct"] == 1
        assert dashboard["total_sessions"] == 1
        assert "topic_breakdown" in dashboard
        assert "badges" in dashboard
        assert "recent_sessions" in dashboard

    def test_persistence(self, tmp_path):
        data_dir = str(tmp_path / "progress")
        pt1 = ProgressTracker(data_dir=data_dir)
        pt1.record_session([{"question_id": "q1", "correct": True}])

        # New instance should load persisted data
        pt2 = ProgressTracker(data_dir=data_dir)
        assert len(pt2.get_history()) == 1


class TestBadgesDefinition:
    def test_badges_list_not_empty(self):
        assert len(BADGES) > 0

    def test_badges_have_required_fields(self):
        for badge in BADGES:
            assert "id" in badge
            assert "name" in badge
            assert "description" in badge
            assert "criteria" in badge

    def test_known_badges_present(self):
        ids = {b["id"] for b in BADGES}
        assert "first_quiz" in ids
        assert "perfect_10" in ids
        assert "week_streak" in ids
        assert "axis_master" in ids
        assert "camera_expert" in ids
