"""Tests for cv.axis module."""

import numpy as np
from cv.axis import frontal_axis_from_image, net_qrs_amplitude


def test_frontal_axis_from_image(synthetic_12lead):
    h, w = synthetic_12lead.shape
    row_h = h // 3
    col_w = w // 4
    # I is at row 0, col 0; aVF is at row 1, col 3
    boxes = {
        "I": (0, 0, col_w, row_h),
        "aVF": (3 * col_w, row_h, 4 * col_w, 2 * row_h),
    }
    rpeaks = {"I": [col_w // 3], "aVF": [col_w // 3]}
    fs_map = {"I": 250.0, "aVF": 250.0}
    result = frontal_axis_from_image(synthetic_12lead, boxes, rpeaks, fs_map)
    assert "angle_deg" in result
    assert "label" in result
    assert "amps" in result
    assert -180 < result["angle_deg"] <= 180


def test_net_qrs_amplitude():
    sig = np.zeros(500, dtype=float)
    sig[250] = 10.0  # R peak
    sig[260] = -3.0  # S wave
    amp = net_qrs_amplitude(sig, 250, 250.0)
    assert isinstance(amp, float)


def test_axis_labels():
    """Test axis label logic for different quadrants."""
    from cv.axis import frontal_axis_from_image

    # Create a minimal gray image
    gray = np.full((200, 400), 200, dtype=np.uint8)

    # Provide boxes and mock data
    boxes = {"I": (0, 0, 200, 100), "aVF": (200, 100, 400, 200)}
    rpeaks = {"I": [], "aVF": []}
    fs_map = {"I": 250.0, "aVF": 250.0}

    result = frontal_axis_from_image(gray, boxes, rpeaks, fs_map)
    assert result["label"] in ["Normal", "Desvio para a esquerda", "Desvio para a direita", "Desvio extremo (noroeste)"]
