"""
Simple SQLite-based persistence layer for ECGiga.

No external dependencies beyond the Python standard library.
Provides user management, quiz result storage, and report persistence.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class Database:
    """Lightweight SQLite wrapper for ECGiga data persistence."""

    def __init__(self, db_path: str = "data/ecgiga.db") -> None:
        self.db_path = db_path
        # Ensure parent directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def init_schema(self) -> None:
        """Create all required tables if they do not already exist."""
        conn = self._get_conn()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id          TEXT PRIMARY KEY,
                username    TEXT UNIQUE NOT NULL,
                email       TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id          TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token       TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                expires_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quiz_results (
                id          TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                quiz_type   TEXT,
                score       REAL,
                total       INTEGER,
                details     TEXT,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reports (
                id          TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title       TEXT,
                report_json TEXT NOT NULL,
                created_at  TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_quiz_user ON quiz_results(user_id);
            CREATE INDEX IF NOT EXISTS idx_reports_user ON reports(user_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
            """
        )
        conn.commit()

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def create_user(self, username: str, email: str, password_hash: str) -> dict:
        """Create a new user and return their record as a dict.

        Raises
        ------
        sqlite3.IntegrityError
            If the username or email already exists.
        """
        conn = self._get_conn()
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO users (id, username, email, password_hash, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, email, password_hash, now, now),
        )
        conn.commit()
        return {
            "id": user_id,
            "username": username,
            "email": email,
            "created_at": now,
        }

    def get_user(self, username: str) -> dict | None:
        """Retrieve a user by username.  Returns ``None`` if not found."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT id, username, email, password_hash, created_at, updated_at "
            "FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)

    # ------------------------------------------------------------------
    # Quiz results
    # ------------------------------------------------------------------

    def save_quiz_result(self, user_id: str, result: dict) -> str:
        """Persist a quiz result.

        Parameters
        ----------
        user_id : str
            The user's UUID.
        result : dict
            Must contain at least ``score`` and ``total``.  May also
            include ``quiz_type`` and arbitrary ``details``.

        Returns
        -------
        str
            The generated result ID.
        """
        conn = self._get_conn()
        result_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO quiz_results (id, user_id, quiz_type, score, total, details, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                result_id,
                user_id,
                result.get("quiz_type", "general"),
                result.get("score", 0),
                result.get("total", 0),
                json.dumps(result.get("details", {}), ensure_ascii=False),
                now,
            ),
        )
        conn.commit()
        return result_id

    def get_quiz_history(self, user_id: str, limit: int = 50) -> list[dict]:
        """Return the most recent quiz results for a user."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT id, quiz_type, score, total, details, created_at "
            "FROM quiz_results WHERE user_id = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        results = []
        for row in rows:
            d = dict(row)
            # Parse JSON details back to dict
            if d.get("details"):
                try:
                    d["details"] = json.loads(d["details"])
                except (json.JSONDecodeError, TypeError):
                    pass
            results.append(d)
        return results

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    def save_report(self, user_id: str, report: dict) -> str:
        """Save an ECG analysis report.

        Parameters
        ----------
        user_id : str
            The user's UUID.
        report : dict
            The full report dictionary (will be stored as JSON).

        Returns
        -------
        str
            The generated report ID.
        """
        conn = self._get_conn()
        report_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        title = report.get("title", report.get("meta", {}).get("src", "Untitled Report"))
        conn.execute(
            "INSERT INTO reports (id, user_id, title, report_json, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                report_id,
                user_id,
                title,
                json.dumps(report, ensure_ascii=False),
                now,
            ),
        )
        conn.commit()
        return report_id

    def get_reports(self, user_id: str) -> list[dict]:
        """Return all reports for a user, newest first."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT id, title, report_json, created_at "
            "FROM reports WHERE user_id = ? "
            "ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        results = []
        for row in rows:
            d = dict(row)
            if d.get("report_json"):
                try:
                    d["report"] = json.loads(d["report_json"])
                except (json.JSONDecodeError, TypeError):
                    d["report"] = {}
            del d["report_json"]
            results.append(d)
        return results
