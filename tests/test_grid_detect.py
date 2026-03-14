"""Tests for cv.grid_detect module."""

import numpy as np
from cv.grid_detect import estimate_grid_period_px


def test_estimate_grid_period_returns_dict(synthetic_gray):
    result = estimate_grid_period_px(synthetic_gray)
    assert isinstance(result, dict)
    assert "confidence" in result


def test_grid_period_detects_small_grid(synthetic_gray):
    result = estimate_grid_period_px(synthetic_gray)
    # At least one axis should detect a period
    px_x = result.get("px_small_x")
    px_y = result.get("px_small_y")
    assert px_x is not None or px_y is not None
    # Period should be positive
    px = px_x or px_y
    assert px > 0


def test_grid_period_big_is_5x_small(synthetic_gray):
    result = estimate_grid_period_px(synthetic_gray)
    px_small = result.get("px_small_x") or result.get("px_small_y")
    px_big = result.get("px_big_x") or result.get("px_big_y")
    if px_small and px_big:
        assert abs(px_big - 5 * px_small) < 1.0


def test_grid_period_rgb(synthetic_pil_image):
    arr = np.asarray(synthetic_pil_image)
    result = estimate_grid_period_px(arr)
    assert isinstance(result, dict)
    assert result.get("confidence", 0) >= 0
