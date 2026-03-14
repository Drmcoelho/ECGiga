"""Tests for persistence module (p29)."""

import tempfile
import os

from persistence.database import Database


def test_create_and_get_user(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.init_schema()
    user = db.create_user("testuser", "test@example.com", "hashed_pw")
    assert user["username"] == "testuser"
    assert user["email"] == "test@example.com"

    loaded = db.get_user("testuser")
    assert loaded is not None
    assert loaded["username"] == "testuser"
    db.close()


def test_get_user_nonexistent(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.init_schema()
    assert db.get_user("nobody") is None
    db.close()


def test_save_and_get_quiz_result(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.init_schema()
    user = db.create_user("quizuser", "quiz@example.com", "hashed_pw")
    result = {"score": 8, "total": 10, "quiz_type": "cameras", "details": {"topic": "leads"}}
    result_id = db.save_quiz_result(user["id"], result)
    assert isinstance(result_id, str)

    history = db.get_quiz_history(user["id"])
    assert len(history) == 1
    assert history[0]["score"] == 8
    assert history[0]["total"] == 10
    db.close()


def test_save_and_get_report(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.init_schema()
    user = db.create_user("analyst", "analyst@example.com", "hashed_pw")
    report = {"intervals": {"PR_ms": 160}, "flags": ["normal"]}
    report_id = db.save_report(user["id"], report)
    assert isinstance(report_id, str)

    reports = db.get_reports(user["id"])
    assert len(reports) == 1
    assert reports[0]["report"]["flags"] == ["normal"]
    db.close()


def test_multiple_quiz_results(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.init_schema()
    user = db.create_user("multi", "multi@example.com", "hashed_pw")
    for i in range(5):
        db.save_quiz_result(user["id"], {"score": i, "total": 10})
    history = db.get_quiz_history(user["id"])
    assert len(history) == 5
    db.close()
