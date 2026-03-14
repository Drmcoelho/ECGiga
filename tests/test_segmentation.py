"""Tests for cv.segmentation and cv.segmentation_ext modules."""

import numpy as np
from cv.segmentation import find_content_bbox, segment_12leads_basic
from cv.segmentation_ext import segment_layout


def test_find_content_bbox(synthetic_gray):
    bbox = find_content_bbox(synthetic_gray)
    assert len(bbox) == 4
    x0, y0, x1, y1 = bbox
    assert x0 < x1
    assert y0 < y1


def test_segment_12leads_basic(synthetic_12lead):
    bbox = find_content_bbox(synthetic_12lead)
    leads = segment_12leads_basic(synthetic_12lead, bbox=bbox)
    assert len(leads) == 12
    for lead in leads:
        assert "lead" in lead
        assert "bbox" in lead
        assert len(lead["bbox"]) == 4


def test_segment_layout_3x4(synthetic_12lead):
    bbox = find_content_bbox(synthetic_12lead)
    leads = segment_layout(synthetic_12lead, layout="3x4", bbox=bbox)
    assert len(leads) == 12
    lead_names = [d["lead"] for d in leads]
    assert "I" in lead_names
    assert "V6" in lead_names


def test_segment_layout_6x2(synthetic_12lead):
    bbox = find_content_bbox(synthetic_12lead)
    leads = segment_layout(synthetic_12lead, layout="6x2", bbox=bbox)
    assert len(leads) == 12


def test_segment_layout_3x4_rhythm(synthetic_12lead):
    bbox = find_content_bbox(synthetic_12lead)
    leads = segment_layout(synthetic_12lead, layout="3x4+rhythm", bbox=bbox)
    assert len(leads) == 13  # 12 + rhythm strip
    assert leads[-1]["lead"] == "II_rhythm"


def test_segment_layout_invalid_raises():
    gray = np.zeros((100, 100), dtype=np.uint8)
    try:
        segment_layout(gray, layout="invalid")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
