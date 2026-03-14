"""Tests for cv.robust_outliers module."""

from cv.robust_outliers import robust_from_intervals


def test_robust_from_intervals_normal():
    intervals_refined = {
        "per_beat": {
            "PR_ms": [160, 162, 158, 161],
            "QRS_ms": [90, 92, 88, 91],
            "QT_ms": [380, 382, 378, 381],
        },
        "median": {"RR_s": 1.0},
    }
    result = robust_from_intervals(intervals_refined)
    assert "beats_total" in result
    assert "beats_used" in result
    assert "median_robust" in result
    assert result["beats_total"] == 4
    assert result["beats_used"] >= 2


def test_robust_from_intervals_with_outlier():
    intervals_refined = {
        "per_beat": {
            "PR_ms": [160, 162, 158, 500],  # 500 is outlier
            "QRS_ms": [90, 92, 88, 300],  # 300 is outlier
            "QT_ms": [380, 382, 378, 900],  # 900 is outlier
        },
        "median": {"RR_s": 1.0},
    }
    result = robust_from_intervals(intervals_refined)
    assert result["beats_used"] < result["beats_total"]


def test_robust_from_intervals_empty():
    result = robust_from_intervals({})
    assert result["beats_total"] == 0
    assert result["beats_used"] == 0
