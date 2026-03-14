"""Tests for cv.normalize module."""

from PIL import Image
from cv.normalize import normalize_scale, estimate_px_per_mm


def test_normalize_scale_returns_tuple(synthetic_pil_image):
    img, scale, pxmm = normalize_scale(synthetic_pil_image, target_px_per_mm=10.0)
    assert isinstance(img, Image.Image)
    assert isinstance(scale, float)


def test_normalize_scale_clamps(synthetic_pil_image):
    _, scale, _ = normalize_scale(synthetic_pil_image, target_px_per_mm=10.0)
    assert 0.5 <= scale <= 2.0


def test_estimate_px_per_mm(synthetic_pil_image):
    pxmm = estimate_px_per_mm(synthetic_pil_image)
    # Should return a positive value or None
    if pxmm is not None:
        assert pxmm > 0
