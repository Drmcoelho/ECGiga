"""
SQLite-based persistence layer for ECGiga.

Thread-safe with connection-per-thread, WAL mode, busy timeout,
schema migration tracking, and proper error handling.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Current schema version — bump when adding migrations
_SCHEMA_VERSION = 2

# ---------------------------------------------------------------------------
# Migrations registry: version -> SQL to apply
# ---------------------------------------------------------------------------

_MIGRATIONS: dict[int, str] = {
    1: """
        CREATE TABLE IF NOT EXISTS users (
            id          TEXT PRIMARY KEY,
            username    TEXT UNIQUE NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role        TEXT NOT NULL DEFAULT 'student',
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
        CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
    """,
    2: """
        CREATE TABLE IF NOT EXISTS study_sessions (
            id          TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            topic       TEXT,
            duration_s  INTEGER,
            score       REAL,
            details     TEXT,
            created_at  TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_study_user ON study_sessions(user_id);
    """,
}


class Database:
    """Thread-safe SQLite wrapper for ECGiga data persistence.

    Each thread gets its own connection via thread-local storage.
    WAL mode is enabled for concurrent read performance.
    Busy timeout prevents immediate failures under contention.
    """

    def __init__(
        self,
        db_path: str = "data/ecgiga.db",
        busy_timeout_ms: int = 5000,
    ) -> None:
        self.db_path = db_path
        self.busy_timeout_ms = busy_timeout_ms
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Connection management (thread-safe)
    # ------------------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        """Return a per-thread connection, creating one if necessary."""
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, timeout=self.busy_timeout_ms / 1000)
            conn.row_factory = sqlite3.Row
            conn.execute(f"PRAGMA busy_timeout = {self.busy_timeout_ms}")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA foreign_keys = ON")
            self._local.conn = conn
        return conn

    def close(self) -> None:
        """Close the current thread's connection."""
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None

    # ------------------------------------------------------------------
    # Schema versioning & migrations
    # ------------------------------------------------------------------

    def _ensure_version_table(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS _schema_version ("
            "  version INTEGER NOT NULL,"
            "  applied_at TEXT NOT NULL"
            ")"
        )
        conn.commit()

    def _current_version(self, conn: sqlite3.Connection) -> int:
        row = conn.execute(
            "SELECT COALESCE(MAX(version), 0) AS v FROM _schema_version"
        ).fetchone()
        return row["v"] if row else 0

    def init_schema(self) -> None:
        """Apply all pending migrations up to _SCHEMA_VERSION."""
        conn = self._get_conn()
        self._ensure_version_table(conn)
        current = self._current_version(conn)

        for version in range(current + 1, _SCHEMA_VERSION + 1):
            sql = _MIGRATIONS.get(version)
            if sql is None:
                raise RuntimeError(f"Missing migration for version {version}")
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO _schema_version (version, applied_at) VALUES (?, ?)",
                (version, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        role: str = "student",
    ) -> dict:
        """Create a new user and return their record as a dict.

        Raises
        ------
        sqlite3.IntegrityError
            If the username or email already exists.
        """
        conn = self._get_conn()
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        try:
            conn.execute(
                "INSERT INTO users (id, username, email, password_hash, role, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, username, email, password_hash, role, now, now),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()
            raise
        return {
            "id": user_id,
            "username": username,
            "email": email,
            "role": role,
            "created_at": now,
        }

    def get_user(self, username: str) -> dict | None:
        """Retrieve a user by username.  Returns ``None`` if not found."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT id, username, email, password_hash, role, created_at, updated_at "
            "FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)

    def get_user_by_id(self, user_id: str) -> dict | None:
        """Retrieve a user by ID."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT id, username, email, role, created_at, updated_at "
            "FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None

    def update_user(self, user_id: str, **fields: Any) -> bool:
        """Update user fields.  Allowed keys: email, password_hash, role."""
        allowed = {"email", "password_hash", "role"}
        to_set = {k: v for k, v in fields.items() if k in allowed}
        if not to_set:
            return False
        to_set["updated_at"] = datetime.now(timezone.utc).isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in to_set)
        values = list(to_set.values()) + [user_id]
        conn = self._get_conn()
        try:
            cur = conn.execute(
                f"UPDATE users SET {set_clause} WHERE id = ?", values  # noqa: S608
            )
            conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error:
            conn.rollback()
            raise

    def delete_user(self, user_id: str) -> bool:
        """Delete a user and all associated data (CASCADE)."""
        conn = self._get_conn()
        cur = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def create_session(self, user_id: str, token: str, expires_at: str) -> str:
        """Create a session record and return the session ID."""
        conn = self._get_conn()
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO sessions (id, user_id, token, created_at, expires_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, user_id, token, now, expires_at),
        )
        conn.commit()
        return session_id

    def get_session_by_token(self, token: str) -> dict | None:
        """Look up a session by its token."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT id, user_id, token, created_at, expires_at "
            "FROM sessions WHERE token = ?",
            (token,),
        ).fetchone()
        return dict(row) if row else None

    def delete_session(self, session_id: str) -> bool:
        """Invalidate a session."""
        conn = self._get_conn()
        cur = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        return cur.rowcount > 0

    def cleanup_expired_sessions(self) -> int:
        """Remove all expired sessions.  Returns count of removed rows."""
        conn = self._get_conn()
        now = datetime.now(timezone.utc).isoformat()
        cur = conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
        conn.commit()
        return cur.rowcount

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
            Must contain at least ``score`` and ``total``.

        Returns
        -------
        str
            The generated result ID.
        """
        conn = self._get_conn()
        result_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        try:
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
        except sqlite3.Error:
            conn.rollback()
            raise
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
            if d.get("details"):
                try:
                    d["details"] = json.loads(d["details"])
                except (json.JSONDecodeError, TypeError):
                    pass
            results.append(d)
        return results

    def get_quiz_stats(self, user_id: str) -> dict:
        """Aggregate quiz statistics for a user."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT COUNT(*) AS total_quizzes, "
            "       COALESCE(AVG(score), 0) AS avg_score, "
            "       COALESCE(MAX(score), 0) AS best_score, "
            "       COALESCE(SUM(total), 0) AS total_questions "
            "FROM quiz_results WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else {}

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    def save_report(self, user_id: str, report: dict) -> str:
        """Save an ECG analysis report."""
        conn = self._get_conn()
        report_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        title = report.get("title", report.get("meta", {}).get("src", "Untitled Report"))
        try:
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
        except sqlite3.Error:
            conn.rollback()
            raise
        return report_id

    def get_reports(self, user_id: str, limit: int = 100) -> list[dict]:
        """Return all reports for a user, newest first."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT id, title, report_json, created_at "
            "FROM reports WHERE user_id = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
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

    def get_report_by_id(self, report_id: str) -> dict | None:
        """Retrieve a single report by its ID."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT id, user_id, title, report_json, created_at "
            "FROM reports WHERE id = ?",
            (report_id,),
        ).fetchone()
        if row is None:
            return None
        d = dict(row)
        try:
            d["report"] = json.loads(d.pop("report_json"))
        except (json.JSONDecodeError, TypeError):
            d["report"] = {}
        return d

    def delete_report(self, report_id: str) -> bool:
        """Delete a report."""
        conn = self._get_conn()
        cur = conn.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        conn.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Study sessions (Phase 26 gamification)
    # ------------------------------------------------------------------

    def save_study_session(self, user_id: str, session_data: dict) -> str:
        """Record a study session for progress tracking."""
        conn = self._get_conn()
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO study_sessions (id, user_id, topic, duration_s, score, details, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                user_id,
                session_data.get("topic", "general"),
                session_data.get("duration_s", 0),
                session_data.get("score"),
                json.dumps(session_data.get("details", {}), ensure_ascii=False),
                now,
            ),
        )
        conn.commit()
        return session_id

    def get_study_sessions(self, user_id: str, limit: int = 100) -> list[dict]:
        """Return study sessions for a user, newest first."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT id, topic, duration_s, score, details, created_at "
            "FROM study_sessions WHERE user_id = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        results = []
        for row in rows:
            d = dict(row)
            if d.get("details"):
                try:
                    d["details"] = json.loads(d["details"])
                except (json.JSONDecodeError, TypeError):
                    pass
            results.append(d)
        return results
