"""Expert review workflow for clinical validation.

Manages the creation of review tasks, collection of expert reviews,
inter-rater agreement calculation, and gold standard derivation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from collections import Counter

from validation.metrics import cohen_kappa, fleiss_kappa


class ReviewWorkflow:
    """Manages expert review tasks for ECG report validation.

    Supports creating review tasks, collecting expert reviews,
    calculating inter-rater agreement, and deriving gold standards.
    """

    def __init__(self):
        self._tasks: dict[str, dict] = {}
        self._reviews: dict[str, list[dict]] = {}  # task_id -> list of reviews

    def create_review_task(self, report: dict, ecg_image_path: str) -> dict:
        """Create a new review task for expert evaluation.

        Args:
            report: The automated ECG analysis report dict
            ecg_image_path: Path to the ECG image for review

        Returns:
            Task dict with id, status, report, and image path.
        """
        task_id = str(uuid.uuid4())
        task = {
            "task_id": task_id,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "report": report,
            "ecg_image_path": ecg_image_path,
            "reviews_count": 0,
        }
        self._tasks[task_id] = task
        self._reviews[task_id] = []
        return task

    def submit_review(self, task_id: str, expert_id: str, review: dict) -> dict:
        """Submit an expert review for a task.

        Args:
            task_id: The task identifier
            expert_id: The reviewing expert's identifier
            review: Dict with review details. Expected keys:
                - findings: list[str] - clinical findings
                - measurements_correct: bool - whether measurements are correct
                - interpretation_correct: bool - whether interpretation is correct
                - flags_correct: bool - whether flags are appropriate
                - overall_rating: int (1-5) - overall quality rating
                - comments: str - free text comments
                - diagnoses: list[str] - expert's diagnoses

        Returns:
            Updated review dict with metadata.

        Raises:
            ValueError: If task_id not found.
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task {task_id} not found")

        review_entry = {
            "review_id": str(uuid.uuid4()),
            "task_id": task_id,
            "expert_id": expert_id,
            "submitted_at": datetime.now().isoformat(),
            **review,
        }

        self._reviews[task_id].append(review_entry)
        self._tasks[task_id]["reviews_count"] = len(self._reviews[task_id])

        if len(self._reviews[task_id]) >= 2:
            self._tasks[task_id]["status"] = "reviewed"

        return review_entry

    def calculate_agreement(self, reviews: list[dict]) -> dict:
        """Calculate inter-rater agreement from multiple reviews.

        Computes Cohen's kappa (for 2 raters) and Fleiss' kappa (for 2+ raters)
        based on binary agreement fields.

        Args:
            reviews: List of review dicts with boolean fields like
                     measurements_correct, interpretation_correct, flags_correct.

        Returns:
            Dict with agreement metrics.
        """
        if len(reviews) < 2:
            return {
                "cohen_kappa": None,
                "fleiss_kappa": None,
                "percent_agreement": None,
                "n_raters": len(reviews),
                "error": "Need at least 2 reviews for agreement calculation",
            }

        # Extract binary ratings for key fields
        fields = ["measurements_correct", "interpretation_correct", "flags_correct"]
        available_fields = [
            f for f in fields if all(f in r for r in reviews)
        ]

        if not available_fields:
            return {
                "cohen_kappa": None,
                "fleiss_kappa": None,
                "percent_agreement": None,
                "n_raters": len(reviews),
                "error": "No common binary fields found in reviews",
            }

        n_raters = len(reviews)
        n_subjects = len(available_fields)

        # Build ratings matrix for Fleiss' kappa
        # Each row = one subject (field), columns = [count_false, count_true]
        fleiss_matrix = []
        agreements = 0
        total_pairs = 0

        for f in available_fields:
            values = [1 if r[f] else 0 for r in reviews]
            true_count = sum(values)
            false_count = n_raters - true_count
            fleiss_matrix.append([false_count, true_count])

            # Pairwise agreement for percent calculation
            for i in range(len(values)):
                for j in range(i + 1, len(values)):
                    total_pairs += 1
                    if values[i] == values[j]:
                        agreements += 1

        percent_agreement = agreements / total_pairs if total_pairs > 0 else 0.0

        # Fleiss' kappa
        fk = fleiss_kappa(fleiss_matrix) if fleiss_matrix else None

        # Cohen's kappa (only for exactly 2 raters)
        ck = None
        if n_raters == 2:
            # Build 2x2 confusion matrix from all fields
            matrix = [[0, 0], [0, 0]]
            for f in available_fields:
                r1 = 1 if reviews[0][f] else 0
                r2 = 1 if reviews[1][f] else 0
                matrix[r1][r2] += 1
            ck = cohen_kappa(matrix)

        # Overall rating agreement
        ratings = [r.get("overall_rating") for r in reviews if "overall_rating" in r]
        rating_agreement = None
        if len(ratings) >= 2:
            mean_rating = sum(ratings) / len(ratings)
            max_diff = max(ratings) - min(ratings)
            rating_agreement = {
                "mean_rating": round(mean_rating, 2),
                "max_difference": max_diff,
                "ratings": ratings,
            }

        return {
            "cohen_kappa": round(ck, 4) if ck is not None else None,
            "fleiss_kappa": round(fk, 4) if fk is not None else None,
            "percent_agreement": round(percent_agreement, 4),
            "n_raters": n_raters,
            "n_subjects": n_subjects,
            "fields_evaluated": available_fields,
            "rating_agreement": rating_agreement,
        }

    def get_gold_standard(self, reviews: list[dict], method: str = "majority") -> dict:
        """Derive a gold standard from multiple expert reviews.

        Args:
            reviews: List of review dicts
            method: Aggregation method - "majority" (default) or "consensus"
                    - majority: use majority vote for each field
                    - consensus: require all to agree, else mark as uncertain

        Returns:
            Gold standard dict with aggregated findings.
        """
        if not reviews:
            return {"error": "No reviews provided"}

        if len(reviews) == 1:
            return {
                "method": "single_reviewer",
                "gold_standard": reviews[0],
                "confidence": "low",
            }

        # Binary fields - majority vote
        binary_fields = ["measurements_correct", "interpretation_correct", "flags_correct"]
        gold = {}

        for field in binary_fields:
            values = [r.get(field) for r in reviews if field in r]
            if not values:
                continue

            if method == "majority":
                true_count = sum(1 for v in values if v)
                gold[field] = true_count > len(values) / 2
                gold[f"{field}_agreement"] = true_count / len(values)
            elif method == "consensus":
                if all(values) or not any(values):
                    gold[field] = values[0]
                    gold[f"{field}_agreement"] = 1.0
                else:
                    gold[field] = None  # uncertain
                    true_count = sum(1 for v in values if v)
                    gold[f"{field}_agreement"] = max(true_count, len(values) - true_count) / len(values)

        # Diagnoses - majority vote
        all_diagnoses: list[str] = []
        for r in reviews:
            all_diagnoses.extend(r.get("diagnoses", []))

        if all_diagnoses:
            diagnosis_counts = Counter(all_diagnoses)
            threshold = len(reviews) / 2
            if method == "majority":
                gold["diagnoses"] = [
                    d for d, count in diagnosis_counts.most_common()
                    if count > threshold
                ]
            elif method == "consensus":
                gold["diagnoses"] = [
                    d for d, count in diagnosis_counts.most_common()
                    if count == len(reviews)
                ]

            gold["all_diagnoses_counts"] = dict(diagnosis_counts)

        # Overall rating - average
        ratings = [r.get("overall_rating") for r in reviews if "overall_rating" in r]
        if ratings:
            gold["overall_rating"] = round(sum(ratings) / len(ratings), 2)

        # Findings - union of all
        all_findings: list[str] = []
        for r in reviews:
            all_findings.extend(r.get("findings", []))
        if all_findings:
            finding_counts = Counter(all_findings)
            if method == "majority":
                gold["findings"] = [
                    f for f, count in finding_counts.most_common()
                    if count > len(reviews) / 2
                ]
            else:
                gold["findings"] = [
                    f for f, count in finding_counts.most_common()
                    if count == len(reviews)
                ]

        # Confidence level
        n = len(reviews)
        if n >= 3:
            confidence = "high"
        elif n == 2:
            confidence = "moderate"
        else:
            confidence = "low"

        return {
            "method": method,
            "n_reviewers": n,
            "gold_standard": gold,
            "confidence": confidence,
        }
