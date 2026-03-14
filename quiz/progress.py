"""Progress tracking and persistence for the ECG quiz system.

Tracks quiz sessions, study streaks, badges/achievements, and provides
dashboard data for visualizing learning progress.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path


BADGES: list[dict] = [
    {
        "id": "first_quiz",
        "name": "First Steps",
        "description": "Complete your first quiz",
        "icon": "star",
        "criteria": "complete_1_quiz",
    },
    {
        "id": "perfect_10",
        "name": "Perfect 10",
        "description": "Get 10 correct answers in a row",
        "icon": "fire",
        "criteria": "streak_10_correct",
    },
    {
        "id": "week_streak",
        "name": "Week Warrior",
        "description": "Study for 7 consecutive days",
        "icon": "calendar",
        "criteria": "study_streak_7",
    },
    {
        "id": "axis_master",
        "name": "Axis Master",
        "description": "Score 90%+ on axis questions",
        "icon": "compass",
        "criteria": "topic_axis_90",
    },
    {
        "id": "camera_expert",
        "name": "Camera Expert",
        "description": "Complete all camera analogy questions",
        "icon": "camera",
        "criteria": "complete_camera_analogy",
    },
    {
        "id": "fifty_questions",
        "name": "Half Century",
        "description": "Answer 50 questions total",
        "icon": "trophy",
        "criteria": "total_50_questions",
    },
    {
        "id": "hundred_questions",
        "name": "Centurion",
        "description": "Answer 100 questions total",
        "icon": "medal",
        "criteria": "total_100_questions",
    },
    {
        "id": "interval_expert",
        "name": "Interval Expert",
        "description": "Score 90%+ on interval questions",
        "icon": "ruler",
        "criteria": "topic_interval_90",
    },
    {
        "id": "rhythm_master",
        "name": "Rhythm Master",
        "description": "Score 90%+ on rhythm questions",
        "icon": "heartbeat",
        "criteria": "topic_rhythm_90",
    },
    {
        "id": "month_streak",
        "name": "Dedicated Learner",
        "description": "Study for 30 consecutive days",
        "icon": "crown",
        "criteria": "study_streak_30",
    },
]


class ProgressTracker:
    """Tracks quiz progress, sessions, streaks, and badges.

    Persists data to a JSON file in the specified directory.
    """

    def __init__(self, data_dir: str = "quiz_progress"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._history_path = self.data_dir / "history.json"
        self._sessions: list[dict] = []
        self._load()

    def _load(self) -> None:
        """Load session history from disk."""
        if self._history_path.exists():
            try:
                data = json.loads(self._history_path.read_text(encoding="utf-8"))
                self._sessions = data.get("sessions", [])
            except (json.JSONDecodeError, TypeError):
                self._sessions = []

    def _save(self) -> None:
        """Save session history to disk."""
        data = {"sessions": self._sessions}
        self._history_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def record_session(self, results: list[dict]) -> None:
        """Save a quiz session.

        Args:
            results: List of dicts with at least:
                - question_id: str
                - correct: bool
                - tag/topic: str (optional)
        """
        session = {
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "results": results,
            "total": len(results),
            "correct": sum(1 for r in results if r.get("correct", False)),
        }
        self._sessions.append(session)
        self._save()

    def get_history(self, topic: str | None = None) -> list[dict]:
        """Get flattened history of all answers, optionally filtered by topic.

        Returns list of individual answer dicts with session timestamp added.
        """
        history = []
        for session in self._sessions:
            for result in session.get("results", []):
                entry = dict(result)
                entry["session_timestamp"] = session.get("timestamp", "")
                entry["session_date"] = session.get("date", "")
                if topic is None or entry.get("tag", entry.get("topic", "")) == topic:
                    history.append(entry)
        return history

    def get_streak(self) -> int:
        """Get current consecutive study streak in days.

        Counts backwards from today (or yesterday if no session today yet).
        """
        if not self._sessions:
            return 0

        study_dates = sorted(set(s.get("date", "") for s in self._sessions if s.get("date")))
        if not study_dates:
            return 0

        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        # Start from today or yesterday
        if today in study_dates:
            current = today
        elif yesterday in study_dates:
            current = yesterday
        else:
            return 0

        streak = 0
        check_date = datetime.strptime(current, "%Y-%m-%d")

        while check_date.strftime("%Y-%m-%d") in study_dates:
            streak += 1
            check_date -= timedelta(days=1)

        return streak

    def get_badges(self) -> list[dict]:
        """Get list of earned badges/achievements.

        Each badge dict includes: id, name, description, icon, earned (bool),
        earned_date (str or None).
        """
        earned = []
        history = self.get_history()
        total_answers = len(history)
        total_correct = sum(1 for h in history if h.get("correct", False))
        streak = self.get_streak()

        # Topic-specific stats
        topic_stats: dict[str, dict] = {}
        for h in history:
            tag = h.get("tag", h.get("topic", "general"))
            if tag not in topic_stats:
                topic_stats[tag] = {"total": 0, "correct": 0}
            topic_stats[tag]["total"] += 1
            if h.get("correct", False):
                topic_stats[tag]["correct"] += 1

        # Calculate max consecutive correct
        max_consecutive = 0
        current_consecutive = 0
        for h in history:
            if h.get("correct", False):
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        for badge_def in BADGES:
            badge = dict(badge_def)
            badge["earned"] = False
            badge["earned_date"] = None
            criteria = badge_def["criteria"]

            if criteria == "complete_1_quiz" and len(self._sessions) >= 1:
                badge["earned"] = True
                badge["earned_date"] = self._sessions[0].get("date")

            elif criteria == "streak_10_correct" and max_consecutive >= 10:
                badge["earned"] = True

            elif criteria == "study_streak_7" and streak >= 7:
                badge["earned"] = True

            elif criteria == "study_streak_30" and streak >= 30:
                badge["earned"] = True

            elif criteria == "topic_axis_90":
                axis_topics = {k: v for k, v in topic_stats.items() if "axis" in k.lower()}
                if axis_topics:
                    total = sum(v["total"] for v in axis_topics.values())
                    correct = sum(v["correct"] for v in axis_topics.values())
                    if total >= 5 and correct / total >= 0.9:
                        badge["earned"] = True

            elif criteria == "complete_camera_analogy":
                camera_topics = {k: v for k, v in topic_stats.items() if "camera" in k.lower()}
                if camera_topics:
                    total = sum(v["total"] for v in camera_topics.values())
                    if total >= 5:  # At least 5 camera analogy questions answered
                        badge["earned"] = True

            elif criteria == "total_50_questions" and total_answers >= 50:
                badge["earned"] = True

            elif criteria == "total_100_questions" and total_answers >= 100:
                badge["earned"] = True

            elif criteria == "topic_interval_90":
                interval_topics = {k: v for k, v in topic_stats.items() if "interval" in k.lower() or "pr" in k.lower() or "qrs" in k.lower() or "qt" in k.lower()}
                if interval_topics:
                    total = sum(v["total"] for v in interval_topics.values())
                    correct = sum(v["correct"] for v in interval_topics.values())
                    if total >= 5 and correct / total >= 0.9:
                        badge["earned"] = True

            elif criteria == "topic_rhythm_90":
                rhythm_topics = {k: v for k, v in topic_stats.items() if "rhythm" in k.lower()}
                if rhythm_topics:
                    total = sum(v["total"] for v in rhythm_topics.values())
                    correct = sum(v["correct"] for v in rhythm_topics.values())
                    if total >= 5 and correct / total >= 0.9:
                        badge["earned"] = True

            earned.append(badge)

        return earned

    def get_dashboard_data(self) -> dict:
        """Get comprehensive data for dashboard display.

        Returns dict with overall stats, streak, badges, recent sessions,
        and topic breakdown.
        """
        history = self.get_history()
        total = len(history)
        correct = sum(1 for h in history if h.get("correct", False))

        # Topic breakdown
        topic_stats: dict[str, dict] = {}
        for h in history:
            tag = h.get("tag", h.get("topic", "general"))
            if tag not in topic_stats:
                topic_stats[tag] = {"total": 0, "correct": 0}
            topic_stats[tag]["total"] += 1
            if h.get("correct", False):
                topic_stats[tag]["correct"] += 1

        for t_stats in topic_stats.values():
            t_stats["accuracy"] = (
                round(t_stats["correct"] / t_stats["total"], 3) if t_stats["total"] > 0 else 0.0
            )

        # Recent sessions (last 5)
        recent = self._sessions[-5:] if len(self._sessions) > 5 else list(self._sessions)
        recent_summary = [
            {
                "date": s.get("date", ""),
                "total": s.get("total", 0),
                "correct": s.get("correct", 0),
                "accuracy": round(s["correct"] / s["total"], 3) if s.get("total", 0) > 0 else 0.0,
            }
            for s in recent
        ]

        badges = self.get_badges()
        earned_badges = [b for b in badges if b["earned"]]

        return {
            "total_questions_answered": total,
            "total_correct": correct,
            "overall_accuracy": round(correct / total, 3) if total > 0 else 0.0,
            "total_sessions": len(self._sessions),
            "streak": self.get_streak(),
            "badges_earned": len(earned_badges),
            "badges_total": len(BADGES),
            "badges": badges,
            "topic_breakdown": topic_stats,
            "recent_sessions": recent_summary,
        }
