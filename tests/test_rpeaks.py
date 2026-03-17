"""Tests for cv.rpeaks_from_image and cv.rpeaks_robust modules."""

import numpy as np
from cv.rpeaks_from_image import (
    extract_trace_centerline,
    smooth_signal,
    detect_rpeaks_from_trace,
    estimate_px_per_sec,
)
from cv.rpeaks_robust import pan_tompkins_like


def test_extract_trace_centerline(synthetic_gray):
    trace = extract_trace_centerline(synthetic_gray)
    assert isinstance(trace, np.ndarray)
    assert trace.ndim == 1
    assert len(trace) == synthetic_gray.shape[1]


def test_smooth_signal():
    sig = np.random.randn(500)
    smoothed = smooth_signal(sig, win=11)
    assert len(smoothed) == len(sig)
    # Smoothed signal should have less variance
    assert np.std(smoothed) <= np.std(sig)


def test_detect_rpeaks_from_trace():
    # Create synthetic trace (y-position in pixels, lower y = higher signal)
    # detect_rpeaks_from_trace inverts, so peaks appear as dips in the position trace
    n = 1000
    t = np.linspace(0, 4, n)
    baseline = 200.0  # baseline y position
    trace = np.full(n, baseline)
    # Add periodic dips (QRS peaks go UP in voltage = DOWN in y-pixel position)
    for peak_t in np.arange(0.4, 4.0, 0.8):
        trace -= 60 * np.exp(-((t - peak_t) ** 2) / (2 * 0.001))
    result = detect_rpeaks_from_trace(trace, px_per_sec=250.0, zthr=1.5)
    assert "peaks_idx" in result
    assert "rr_sec" in result
    assert len(result["peaks_idx"]) >= 2


def test_estimate_px_per_sec():
    assert estimate_px_per_sec(10.0, 25.0) == 250.0
    assert estimate_px_per_sec(None, 25.0) is None


def test_pan_tompkins_like():
    # Create synthetic trace with periodic QRS complexes
    n = 2000
    t = np.linspace(0, 8, n)
    trace = np.zeros(n)
    for peak_t in np.arange(0.5, 8.0, 1.0):
        trace += 40 * np.exp(-((t - peak_t) ** 2) / (2 * 0.0005))
    result = pan_tompkins_like(trace, px_per_sec=250.0)
    assert "peaks_idx" in result
    assert "fs_px" in result
    assert "signals" in result
    assert "params" in result
    assert len(result["peaks_idx"]) >= 2


def test_pan_tompkins_like_ignores_boundary_artifact():
    trace = np.zeros(500)
    trace[0] = 500.0
    trace[200] = 40.0
    trace[350] = 40.0
    result = pan_tompkins_like(trace, px_per_sec=250.0)
    assert 0 not in result["peaks_idx"]
