"""Shared test fixtures for ECGiga test suite."""

import pytest


@pytest.fixture
def sample_report():
    """A sample ECG report dict used across multiple test modules."""
    return {
        "version": "0.5.0",
        "meta": {"src": "test_ecg.png", "date": "2024-01-01"},
        "intervals": {
            "median": {
                "RR_s": 0.8,
                "PR_ms": 160,
                "QRS_ms": 90,
                "QT_ms": 380,
                "QTc_B": 425,
            }
        },
        "intervals_refined": {
            "median": {
                "RR_s": 0.8,
                "PR_ms": 160,
                "QRS_ms": 90,
                "QT_ms": 380,
                "QTc_B": 425,
            }
        },
        "axis": {"angle_deg": 60, "label": "normal"},
        "rhythm": "sinusal",
        "rate_bpm": 75,
        "flags": ["Ritmo sinusal normal"],
    }
