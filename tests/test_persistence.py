"""Tests for the persistence module (Phase 29).

Covers:
- Database init_schema creates tables
- create_user and get_user
- save/get quiz results
- save/get reports
- hash_password and verify_password
- generate_token and verify_token
"""

from __future__ import annotations

import sqlite3

import pytest

from persistence.database import Database
from persistence.auth import (
    hash_password,
    verify_password,
    generate_token,
    verify_token,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db(tmp_path):
    """Create a temporary Database with initialized schema."""
    database = Database(db_path=str(tmp_path / "test_ecgiga.db"))
    database.init_schema()
    yield database
    database.close()


@pytest.fixture
def user_in_db(db):
    """Create a test user and return (db, user_dict)."""
    pw_hash = hash_password("test_password_123")
    user = db.create_user("testuser", "test@example.com", pw_hash)
    return db, user


# ---------------------------------------------------------------------------
# Database schema
# ---------------------------------------------------------------------------


def test_init_schema_creates_tables(db):
    """init_schema should create users, sessions, quiz_results, reports tables."""
    conn = db._get_conn()
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = {row["name"] for row in cursor.fetchall()}
    assert "users" in tables
    assert "sessions" in tables
    assert "quiz_results" in tables
    assert "reports" in tables


def test_init_schema_idempotent(db):
    """Calling init_schema twice should not raise."""
    db.init_schema()
    conn = db._get_conn()
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row["name"] for row in cursor.fetchall()}
    assert "users" in tables


def test_indexes_created(db):
    """Expected indexes should exist."""
    conn = db._get_conn()
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
    )
    indexes = {row["name"] for row in cursor.fetchall()}
    assert "idx_quiz_user" in indexes
    assert "idx_reports_user" in indexes
    assert "idx_sessions_user" in indexes


# ---------------------------------------------------------------------------
# create_user and get_user
# ---------------------------------------------------------------------------


def test_create_user(db):
    """create_user returns a dict with id, username, email, created_at."""
    user = db.create_user("alice", "alice@example.com", "hash123")
    assert "id" in user
    assert user["username"] == "alice"
    assert user["email"] == "alice@example.com"
    assert "created_at" in user


def test_get_user(db):
    """get_user retrieves a previously created user."""
    db.create_user("bob", "bob@example.com", "hash456")
    user = db.get_user("bob")
    assert user is not None
    assert user["username"] == "bob"
    assert user["email"] == "bob@example.com"
    assert "password_hash" in user


def test_get_user_not_found(db):
    """get_user returns None for non-existent user."""
    assert db.get_user("nonexistent") is None


def test_create_duplicate_username_raises(db):
    """Duplicate username should raise IntegrityError."""
    db.create_user("charlie", "charlie@example.com", "hash")
    with pytest.raises(sqlite3.IntegrityError):
        db.create_user("charlie", "charlie2@example.com", "hash")


def test_create_duplicate_email_raises(db):
    """Duplicate email should raise IntegrityError."""
    db.create_user("dave", "dave@example.com", "hash")
    with pytest.raises(sqlite3.IntegrityError):
        db.create_user("dave2", "dave@example.com", "hash")


# ---------------------------------------------------------------------------
# Quiz results
# ---------------------------------------------------------------------------


def test_save_and_get_quiz_result(user_in_db):
    """save_quiz_result + get_quiz_history should round-trip."""
    db, user = user_in_db
    result = {
        "quiz_type": "arritmias",
        "score": 8,
        "total": 10,
        "details": {"wrong_questions": ["q3", "q7"]},
    }
    result_id = db.save_quiz_result(user["id"], result)
    assert isinstance(result_id, str) and len(result_id) > 0

    history = db.get_quiz_history(user["id"])
    assert len(history) == 1
    assert history[0]["score"] == 8
    assert history[0]["total"] == 10
    assert history[0]["quiz_type"] == "arritmias"
    assert history[0]["details"]["wrong_questions"] == ["q3", "q7"]


def test_quiz_history_ordering(user_in_db):
    """Results should be returned newest first."""
    db, user = user_in_db
    db.save_quiz_result(user["id"], {"score": 5, "total": 10})
    db.save_quiz_result(user["id"], {"score": 9, "total": 10})
    history = db.get_quiz_history(user["id"])
    assert len(history) == 2
    assert history[0]["score"] == 9


def test_quiz_history_limit(user_in_db):
    """get_quiz_history should respect the limit parameter."""
    db, user = user_in_db
    for i in range(5):
        db.save_quiz_result(user["id"], {"score": i, "total": 10})
    history = db.get_quiz_history(user["id"], limit=3)
    assert len(history) == 3


def test_quiz_history_empty(user_in_db):
    """New user should have empty quiz history."""
    db, user = user_in_db
    history = db.get_quiz_history(user["id"])
    assert history == []


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


def test_save_and_get_report(user_in_db):
    """save_report + get_reports should round-trip."""
    db, user = user_in_db
    report = {
        "title": "ECG Analysis #1",
        "meta": {"src": "ecg.png"},
        "intervals": {"PR_ms": 160, "QRS_ms": 90},
    }
    report_id = db.save_report(user["id"], report)
    assert isinstance(report_id, str)

    reports = db.get_reports(user["id"])
    assert len(reports) == 1
    assert reports[0]["title"] == "ECG Analysis #1"
    assert reports[0]["report"]["intervals"]["PR_ms"] == 160


def test_reports_empty(user_in_db):
    """New user should have no reports."""
    db, user = user_in_db
    assert db.get_reports(user["id"]) == []


def test_multiple_reports_ordering(user_in_db):
    """Multiple reports should be returned newest first."""
    db, user = user_in_db
    db.save_report(user["id"], {"title": "First"})
    db.save_report(user["id"], {"title": "Second"})
    reports = db.get_reports(user["id"])
    assert len(reports) == 2
    assert reports[0]["title"] == "Second"


# ---------------------------------------------------------------------------
# hash_password and verify_password
# ---------------------------------------------------------------------------


def test_hash_password_format():
    """Hashed password should be in salt_hex:hash_hex format."""
    hashed = hash_password("my_password")
    assert ":" in hashed
    salt_hex, hash_hex = hashed.split(":", 1)
    assert len(salt_hex) == 32  # 16 bytes hex
    assert len(hash_hex) == 64  # SHA-256 hex


def test_verify_password_correct():
    """Correct password should verify."""
    hashed = hash_password("correct_horse_battery_staple")
    assert verify_password("correct_horse_battery_staple", hashed) is True


def test_verify_password_wrong():
    """Wrong password should fail."""
    hashed = hash_password("right_password")
    assert verify_password("wrong_password", hashed) is False


def test_hash_uniqueness():
    """Same password hashed twice should produce different outputs (different salts)."""
    h1 = hash_password("same_pw")
    h2 = hash_password("same_pw")
    assert h1 != h2


def test_verify_password_invalid_format():
    """Invalid hash format should return False, not crash."""
    assert verify_password("test", "invalid") is False
    assert verify_password("test", "") is False
    assert verify_password("test", "no_colon_here") is False


# ---------------------------------------------------------------------------
# generate_token and verify_token
# ---------------------------------------------------------------------------


def test_generate_token_format():
    """Token should have three dot-separated parts."""
    token = generate_token("user-123", secret="test-secret")
    assert len(token.split(".")) == 3


def test_verify_token_roundtrip():
    """generate_token + verify_token should round-trip the user ID."""
    secret = "my-test-secret"
    token = generate_token("user-456", secret=secret)
    payload = verify_token(token, secret=secret)
    assert payload["sub"] == "user-456"
    assert "iat" in payload
    assert "exp" in payload


def test_verify_token_wrong_secret():
    """Wrong secret should raise ValueError."""
    token = generate_token("user-789", secret="secret-a")
    with pytest.raises(ValueError, match="Invalid token signature"):
        verify_token(token, secret="secret-b")


def test_verify_token_malformed():
    """Malformed tokens should raise ValueError."""
    with pytest.raises(ValueError, match="3 parts"):
        verify_token("not.a.valid.token.at.all")
    with pytest.raises(ValueError, match="3 parts"):
        verify_token("single_part")


def test_verify_token_expired():
    """Expired token should raise ValueError."""
    import persistence.auth as auth_mod

    original_ttl = auth_mod._TOKEN_TTL_SECONDS
    try:
        auth_mod._TOKEN_TTL_SECONDS = -1
        token = generate_token("user-expired", secret="test")
        with pytest.raises(ValueError, match="expired"):
            verify_token(token, secret="test")
    finally:
        auth_mod._TOKEN_TTL_SECONDS = original_ttl
