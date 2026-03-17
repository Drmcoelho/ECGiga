"""Tests for adaptive quiz integration (CLI, MCP, and web app wiring)."""

import json
import pytest
import tempfile
import pathlib


def test_adaptive_engine_selects_from_bank():
    """AdaptiveEngine loads bank and selects questions."""
    from quiz.adaptive import AdaptiveEngine

    engine = AdaptiveEngine(quiz_bank_path="quiz/bank")
    assert len(engine._questions) > 0

    q = engine.select_next_question([])
    assert "id" in q
    assert "stem" in q
    assert "options" in q


def test_adaptive_engine_avoids_repeated_questions():
    """AdaptiveEngine avoids selecting same question twice."""
    from quiz.adaptive import AdaptiveEngine

    engine = AdaptiveEngine(quiz_bank_path="quiz/bank")
    history = []
    seen_ids = set()

    for _ in range(5):
        q = engine.select_next_question(history)
        qid = q.get("id", "")
        assert qid not in seen_ids, f"Duplicate question: {qid}"
        seen_ids.add(qid)
        history.append({
            "question_id": qid,
            "correct": True,
            "tag": q.get("tag", q.get("topic", "general")),
        })


def test_spaced_repetition_persistence(tmp_path):
    """SpacedRepetitionScheduler persists state to disk."""
    from quiz.spaced_repetition import SpacedRepetitionScheduler

    sr_path = str(tmp_path / "sr_state.json")
    sr = SpacedRepetitionScheduler(data_path=sr_path)
    sr.record_answer("q1", quality=5)
    sr.record_answer("q2", quality=1)

    # Reload from disk
    sr2 = SpacedRepetitionScheduler(data_path=sr_path)
    stats = sr2.get_stats()
    assert stats["total_questions"] == 2
    assert stats["total_reviews"] == 2


def test_progress_tracker_session(tmp_path):
    """ProgressTracker records sessions and computes dashboard."""
    from quiz.progress import ProgressTracker

    tracker = ProgressTracker(data_dir=str(tmp_path / "progress"))
    tracker.record_session([
        {"question_id": "q1", "correct": True, "tag": "axis"},
        {"question_id": "q2", "correct": False, "tag": "intervals"},
        {"question_id": "q3", "correct": True, "tag": "axis"},
    ])

    dashboard = tracker.get_dashboard_data()
    assert dashboard["total_questions_answered"] == 3
    assert dashboard["total_correct"] == 2
    assert dashboard["streak"] >= 1
    assert "axis" in dashboard["topic_breakdown"]
    assert dashboard["topic_breakdown"]["axis"]["accuracy"] == 1.0


def test_progress_tracker_badges(tmp_path):
    """ProgressTracker awards 'first_quiz' badge after first session."""
    from quiz.progress import ProgressTracker

    tracker = ProgressTracker(data_dir=str(tmp_path / "progress"))
    tracker.record_session([
        {"question_id": "q1", "correct": True, "tag": "axis"},
    ])

    badges = tracker.get_badges()
    first = next(b for b in badges if b["id"] == "first_quiz")
    assert first["earned"] is True


def test_full_adaptive_flow(tmp_path):
    """End-to-end: select questions, record to SR and progress."""
    from quiz.adaptive import AdaptiveEngine
    from quiz.spaced_repetition import SpacedRepetitionScheduler
    from quiz.progress import ProgressTracker

    engine = AdaptiveEngine(quiz_bank_path="quiz/bank")
    sr = SpacedRepetitionScheduler(data_path=str(tmp_path / "sr.json"))
    tracker = ProgressTracker(data_dir=str(tmp_path / "progress"))

    history = tracker.get_history()
    results = []

    for _ in range(3):
        q = engine.select_next_question(history)
        assert q
        qid = q["id"]
        correct = True  # simulate correct answer
        sr.record_answer(qid, quality=5 if correct else 1)
        results.append({
            "question_id": qid,
            "correct": correct,
            "tag": q.get("tag", q.get("topic", "general")),
        })
        history.append(results[-1])

    tracker.record_session(results)

    # Verify state
    sr_stats = sr.get_stats()
    assert sr_stats["total_questions"] == 3
    assert sr_stats["total_reviews"] == 3

    dashboard = tracker.get_dashboard_data()
    assert dashboard["total_questions_answered"] == 3
    assert dashboard["total_sessions"] == 1

    report = engine.generate_progress_report(history)
    assert report["total_questions"] == 3
    assert report["overall_accuracy"] == 1.0


def test_mcp_quiz_adaptive_uses_adaptive_engine():
    """MCP /quiz_adaptive endpoint returns questions from AdaptiveEngine."""
    from fastapi.testclient import TestClient
    from mcp_server import app

    client = TestClient(app)
    resp = client.post("/quiz_adaptive", json={
        "n_questions": 3,
        "seed": 42,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["questions"]) == 3
    assert len(data["tags"]) >= 1
    for q in data["questions"]:
        assert "id" in q
        assert "stem" in q


def test_mcp_quiz_adaptive_with_report():
    """MCP /quiz_adaptive with report context biases question selection."""
    from fastapi.testclient import TestClient
    from mcp_server import app

    client = TestClient(app)
    resp = client.post("/quiz_adaptive", json={
        "report": {"intervals_refined": {"median": {"QRS_ms": 140}}},
        "n_questions": 3,
        "seed": 42,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["questions"]) >= 1
