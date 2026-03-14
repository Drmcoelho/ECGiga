"""Tests for cv.deskew module."""

from PIL import Image
import numpy as np
from cv.deskew import estimate_rotation_angle, rotate_image


def test_estimate_rotation_returns_dict(synthetic_pil_image):
    result = estimate_rotation_angle(synthetic_pil_image, search_deg=3.0, step=1.0)
    assert isinstance(result, dict)
    assert "angle_deg" in result
    assert "score" in result
    assert "score0" in result


def test_no_rotation_near_zero(synthetic_pil_image):
    result = estimate_rotation_angle(synthetic_pil_image, search_deg=3.0, step=1.0)
    # Synthetic image should need little to no rotation
    assert abs(result["angle_deg"]) <= 3.0


def test_rotate_image_returns_image(synthetic_pil_image):
    out = rotate_image(synthetic_pil_image, 2.0)
    assert isinstance(out, Image.Image)


def test_rotate_zero_preserves_size(synthetic_pil_image):
    out = rotate_image(synthetic_pil_image, 0.0)
    # With expand=True and angle=0, size should be same
    assert out.size == synthetic_pil_image.size
