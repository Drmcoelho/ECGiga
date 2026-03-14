"""Tests for cv.intervals and cv.intervals_refined modules."""

import numpy as np
from cv.intervals import intervals_from_trace
from cv.intervals_refined import intervals_refined_from_trace


def _make_trace_with_peaks(n=2000, fs=250.0):
    """Create a synthetic trace with known QRS peaks."""
    t = np.linspace(0, n / fs, n)
    trace = np.zeros(n)
    peak_positions = []
    for peak_t in np.arange(0.5, n / fs - 0.5, 1.0):
        idx = int(peak_t * fs)
        peak_positions.append(idx)
        trace += 40 * np.exp(-((t - peak_t) ** 2) / (2 * 0.0005))
        # Add P wave
        trace += 5 * np.exp(-((t - (peak_t - 0.16)) ** 2) / (2 * 0.001))
        # Add T wave
        trace += 10 * np.exp(-((t - (peak_t + 0.25)) ** 2) / (2 * 0.005))
    return trace, peak_positions


def test_intervals_from_trace():
    trace, peaks = _make_trace_with_peaks()
    result = intervals_from_trace(trace, peaks, px_per_sec=250.0)
    assert "per_beat" in result
    assert "median" in result
    med = result["median"]
    assert "QRS_ms" in med
    assert "QTc_B" in med
    assert "RR_s" in med
    # RR should be ~1.0s
    if med["RR_s"] is not None:
        assert 0.5 < med["RR_s"] < 2.0


def test_intervals_refined_from_trace():
    trace, peaks = _make_trace_with_peaks()
    result = intervals_refined_from_trace(trace, peaks, px_per_sec=250.0)
    assert "method" in result
    assert result["method"] == "multi_evidence_v1"
    assert "per_beat" in result
    assert "median" in result
    med = result["median"]
    assert "QRS_ms" in med
    assert "QTc_B" in med


def test_intervals_empty_peaks():
    trace = np.random.randn(500)
    result = intervals_from_trace(trace, [], px_per_sec=250.0)
    assert result["median"]["RR_s"] is None
