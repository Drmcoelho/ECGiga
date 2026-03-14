"""SM-2 based spaced repetition algorithm for ECG quiz learning.

Implements a spaced repetition scheduler that tracks question states
and determines optimal review timing based on the SM-2 algorithm.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class QuestionState:
    """State of a single question in the spaced repetition system."""

    ease_factor: float = 2.5
    interval: int = 1  # days
    repetitions: int = 0
    next_review: str = ""  # ISO format date string
    last_quality: int = 0
    total_reviews: int = 0
    correct_count: int = 0

    def __post_init__(self):
        if not self.next_review:
            self.next_review = datetime.now().strftime("%Y-%m-%d")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "QuestionState":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class SpacedRepetitionScheduler:
    """SM-2 based spaced repetition scheduler.

    Tracks question states and determines which questions are due for review,
    adjusting intervals based on answer quality (0-5 SM-2 scale).
    """

    def __init__(self, data_path: str = "quiz_progress.json"):
        self.data_path = data_path
        self._states: dict[str, QuestionState] = {}
        self.load()

    def record_answer(self, question_id: str, quality: int) -> None:
        """Record an answer for a question using SM-2 algorithm.

        Args:
            question_id: Unique identifier for the question
            quality: Answer quality on SM-2 scale (0-5):
                0 - Complete blackout
                1 - Wrong, but recognized answer
                2 - Wrong, but easy to recall
                3 - Correct with serious difficulty
                4 - Correct with some hesitation
                5 - Perfect response
        """
        quality = max(0, min(5, quality))

        if question_id not in self._states:
            self._states[question_id] = QuestionState()

        state = self._states[question_id]
        state.total_reviews += 1
        state.last_quality = quality

        if quality >= 3:
            state.correct_count += 1

        # SM-2 algorithm
        if quality < 3:
            # Failed: reset repetitions
            state.repetitions = 0
            state.interval = 1
        else:
            if state.repetitions == 0:
                state.interval = 1
            elif state.repetitions == 1:
                state.interval = 6
            else:
                state.interval = round(state.interval * state.ease_factor)
            state.repetitions += 1

        # Update ease factor
        state.ease_factor = max(
            1.3,
            state.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
        )

        # Set next review date
        state.next_review = (datetime.now() + timedelta(days=state.interval)).strftime("%Y-%m-%d")
        self.save()

    def get_due_questions(self, n: int = 10) -> list[str]:
        """Get up to n questions that are due for review.

        Returns question IDs sorted by urgency (most overdue first).
        """
        today = datetime.now().strftime("%Y-%m-%d")
        due = []

        for qid, state in self._states.items():
            if state.next_review <= today:
                due.append((qid, state.next_review))

        # Sort by review date (most overdue first)
        due.sort(key=lambda x: x[1])
        return [qid for qid, _ in due[:n]]

    def get_stats(self) -> dict:
        """Get performance statistics across all tracked questions."""
        if not self._states:
            return {
                "total_questions": 0,
                "total_reviews": 0,
                "average_ease_factor": 2.5,
                "due_today": 0,
                "mastered": 0,
                "learning": 0,
                "accuracy": 0.0,
            }

        today = datetime.now().strftime("%Y-%m-%d")
        total_reviews = sum(s.total_reviews for s in self._states.values())
        total_correct = sum(s.correct_count for s in self._states.values())
        due = sum(1 for s in self._states.values() if s.next_review <= today)
        mastered = sum(1 for s in self._states.values() if s.repetitions >= 3 and s.ease_factor >= 2.0)
        learning = len(self._states) - mastered

        return {
            "total_questions": len(self._states),
            "total_reviews": total_reviews,
            "average_ease_factor": sum(s.ease_factor for s in self._states.values()) / len(self._states),
            "due_today": due,
            "mastered": mastered,
            "learning": learning,
            "accuracy": total_correct / total_reviews if total_reviews > 0 else 0.0,
        }

    def save(self) -> None:
        """Persist scheduler state to JSON file."""
        data = {qid: state.to_dict() for qid, state in self._states.items()}
        Path(self.data_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.data_path).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self) -> None:
        """Load scheduler state from JSON file."""
        path = Path(self.data_path)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self._states = {
                    qid: QuestionState.from_dict(state_dict)
                    for qid, state_dict in data.items()
                }
            except (json.JSONDecodeError, TypeError):
                self._states = {}
        else:
            self._states = {}
