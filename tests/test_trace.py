"""Tests for cv.trace re-export module."""

from cv.trace import extract_trace_centerline, smooth_signal
import numpy as np


def test_trace_imports():
    """Verify that cv.trace properly re-exports from cv.rpeaks_from_image."""
    from cv import rpeaks_from_image

    assert extract_trace_centerline is rpeaks_from_image.extract_trace_centerline
    assert smooth_signal is rpeaks_from_image.smooth_signal


def test_extract_trace_via_trace_module(synthetic_gray):
    trace = extract_trace_centerline(synthetic_gray)
    assert isinstance(trace, np.ndarray)
    assert trace.ndim == 1
