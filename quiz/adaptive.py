"""Adaptive difficulty engine for ECG quiz.

Selects questions based on student performance history, estimates ability,
and recommends topics for improvement.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from collections import defaultdict


class AdaptiveEngine:
    """Adaptive difficulty engine that selects questions based on performance.

    Uses performance history to estimate student ability and select
    questions at an appropriate difficulty level targeting a specific accuracy.
    """

    def __init__(self, quiz_bank_path: str = "quiz/bank"):
        self.quiz_bank_path = Path(quiz_bank_path)
        self._questions: list[dict] = []
        self._load_bank()

    def _load_bank(self) -> None:
        """Load all questions from the quiz bank directory."""
        self._questions = []
        if not self.quiz_bank_path.exists():
            return

        for json_file in sorted(self.quiz_bank_path.rglob("*.json")):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    if "questions" in data:
                        for q in data["questions"]:
                            q.setdefault("source_file", str(json_file))
                            self._questions.append(q)
                    elif "id" in data:
                        data.setdefault("source_file", str(json_file))
                        self._questions.append(data)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            item.setdefault("source_file", str(json_file))
                            self._questions.append(item)
            except (json.JSONDecodeError, OSError):
                continue

    def select_next_question(
        self, history: list[dict], target_accuracy: float = 0.7
    ) -> dict:
        """Select the next question based on performance history.

        Prioritizes:
        1. Questions on weak topics (low accuracy)
        2. Questions not yet attempted
        3. Questions at appropriate difficulty for target accuracy

        Args:
            history: List of dicts with keys: question_id, correct (bool), tag/topic
            target_accuracy: Target accuracy level (0-1), default 0.7

        Returns:
            A question dict from the bank, or empty dict if bank is empty.
        """
        if not self._questions:
            return {}

        # Analyze history
        attempted_ids = {h.get("question_id") for h in history}
        topic_stats = self._compute_topic_stats(history)
        ability = self.estimate_ability(history)

        # Find weak topics
        weak_topics = []
        for topic, stats in topic_stats.items():
            if stats["total"] >= 2 and stats["accuracy"] < target_accuracy:
                weak_topics.append(topic)

        # Score each question
        scored = []
        for q in self._questions:
            qid = q.get("id", "")
            tag = q.get("tag", q.get("topic", "general"))
            score = 0.0

            # Prefer unattempted questions
            if qid not in attempted_ids:
                score += 2.0

            # Prefer questions on weak topics
            if tag in weak_topics:
                score += 3.0

            # Prefer questions matching ability level
            raw_diff = q.get("difficulty", 0.5)
            if isinstance(raw_diff, str):
                difficulty = {"easy": 0.3, "medium": 0.5, "hard": 0.7, "expert": 0.9}.get(raw_diff.lower(), 0.5)
            else:
                difficulty = float(raw_diff)
            diff_match = 1.0 - abs(difficulty - ability)
            score += diff_match

            # Add small random factor to avoid repetitive ordering
            score += random.random() * 0.5

            scored.append((score, q))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1] if scored else {}

    def estimate_ability(self, history: list[dict]) -> float:
        """Estimate student ability level from history.

        Returns a value between 0 and 1, where:
        - 0 = beginner
        - 0.5 = intermediate
        - 1.0 = expert

        Uses exponential weighting to emphasize recent performance.
        """
        if not history:
            return 0.5

        # Exponential weighting: more recent answers have more weight
        total_weight = 0.0
        weighted_correct = 0.0
        n = len(history)

        for i, entry in enumerate(history):
            # More recent entries get higher weight
            weight = 1.0 + (i / n) * 2.0  # weight ranges from 1.0 to 3.0
            total_weight += weight
            if entry.get("correct", False):
                weighted_correct += weight

        raw_ability = weighted_correct / total_weight if total_weight > 0 else 0.5

        # Adjust for sample size: pull toward 0.5 with few data points
        confidence = min(1.0, n / 20.0)
        ability = 0.5 * (1 - confidence) + raw_ability * confidence

        return max(0.0, min(1.0, ability))

    def recommend_topics(self, history: list[dict]) -> list[str]:
        """Recommend weak topics that need more study.

        Returns topics sorted by accuracy (lowest first), filtered to
        those below 70% accuracy with at least 2 attempts.
        """
        topic_stats = self._compute_topic_stats(history)
        weak = []

        for topic, stats in topic_stats.items():
            if stats["total"] >= 2 and stats["accuracy"] < 0.7:
                weak.append((topic, stats["accuracy"]))

        # Sort by accuracy ascending (weakest first)
        weak.sort(key=lambda x: x[1])
        return [topic for topic, _ in weak]

    def generate_progress_report(self, history: list[dict]) -> dict:
        """Generate a comprehensive progress report from history.

        Returns dict with ability estimate, topic breakdown, strengths,
        weaknesses, and recommendations.
        """
        topic_stats = self._compute_topic_stats(history)
        ability = self.estimate_ability(history)
        weak_topics = self.recommend_topics(history)

        total = len(history)
        correct = sum(1 for h in history if h.get("correct", False))
        accuracy = correct / total if total > 0 else 0.0

        # Identify strong topics (>= 80% with at least 3 attempts)
        strong_topics = [
            topic
            for topic, stats in topic_stats.items()
            if stats["total"] >= 3 and stats["accuracy"] >= 0.8
        ]

        # Recent trend (last 10)
        recent = history[-10:] if len(history) >= 10 else history
        recent_correct = sum(1 for h in recent if h.get("correct", False))
        recent_accuracy = recent_correct / len(recent) if recent else 0.0

        # Determine trend
        if len(history) >= 20:
            first_half = history[: len(history) // 2]
            second_half = history[len(history) // 2 :]
            first_acc = sum(1 for h in first_half if h.get("correct")) / len(first_half)
            second_acc = sum(1 for h in second_half if h.get("correct")) / len(second_half)
            if second_acc > first_acc + 0.05:
                trend = "improving"
            elif second_acc < first_acc - 0.05:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "ability": round(ability, 3),
            "total_questions": total,
            "total_correct": correct,
            "overall_accuracy": round(accuracy, 3),
            "recent_accuracy": round(recent_accuracy, 3),
            "trend": trend,
            "topic_breakdown": {
                topic: {
                    "accuracy": round(stats["accuracy"], 3),
                    "total": stats["total"],
                    "correct": stats["correct"],
                }
                for topic, stats in topic_stats.items()
            },
            "strong_topics": strong_topics,
            "weak_topics": weak_topics,
            "recommendations": [
                f"Focus on: {t}" for t in weak_topics[:3]
            ] if weak_topics else ["Great job! Keep reviewing all topics."],
        }

    def _compute_topic_stats(self, history: list[dict]) -> dict[str, dict]:
        """Compute per-topic accuracy stats from history."""
        stats: dict[str, dict] = defaultdict(lambda: {"correct": 0, "total": 0, "accuracy": 0.0})

        for entry in history:
            topic = entry.get("tag", entry.get("topic", "general"))
            stats[topic]["total"] += 1
            if entry.get("correct", False):
                stats[topic]["correct"] += 1

        for topic in stats:
            total = stats[topic]["total"]
            stats[topic]["accuracy"] = stats[topic]["correct"] / total if total > 0 else 0.0

        return dict(stats)
