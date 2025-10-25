"""
Test basic ingest inline functionality.

Tests the /ecg/process-inline endpoint with small synthetic images,
verifying report structure and version compatibility.
"""

import io
import os
import sys

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../"))

from api.main import app

client = TestClient(app)


def create_test_image(width=400, height=300, format="PNG"):
    """Create a simple synthetic ECG-like image for testing."""
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # Draw some simple grid lines
    for x in range(0, width, 20):
        draw.line([(x, 0), (x, height)], fill="lightgray", width=1)
    for y in range(0, height, 20):
        draw.line([(0, y), (width, y)], fill="lightgray", width=1)

    # Draw a simple ECG-like trace
    points = []
    for x in range(0, width, 5):
        # Simple sine wave with some spikes to mimic ECG
        y = height // 2 + int(20 * (1.5 * (x % 100 < 5) - 0.2))
        points.append((x, y))

    if len(points) > 1:
        draw.line(points, fill="black", width=2)

    # Save to bytes
    img_buffer = io.BytesIO()
    img.save(img_buffer, format=format)
    img_buffer.seek(0)
    return img_buffer.getvalue()


def test_health_endpoint():
    """Test API health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root_endpoint():
    """Test API root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "ECG Course API"
    assert "endpoints" in data


def test_process_inline_basic():
    """Test basic image processing without persistence."""
    image_data = create_test_image()

    response = client.post(
        "/ecg/process-inline",
        files={"file": ("test.png", image_data, "image/png")},
        data={
            "deskew": "false",
            "normalize": "false",
            "auto_grid": "false",
            "rpeaks_robust": "false",
            "intervals": "false",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "summary" in data
    assert "report" in data

    # Check summary
    summary = data["summary"]
    assert "version" in summary
    assert "capabilities" in summary
    assert isinstance(summary["capabilities"], list)
    assert "processing_successful" in summary

    # Check report structure
    report = data["report"]
    assert "version" in report
    assert "capabilities" in report
    assert "meta" in report
    assert "measures" in report
    assert "flags" in report

    # Verify schema version
    assert report["version"] in ["0.4.0", "0.5.0"]


def test_process_inline_with_auto_grid():
    """Test image processing with auto grid detection enabled."""
    image_data = create_test_image()

    response = client.post(
        "/ecg/process-inline",
        files={"file": ("test.png", image_data, "image/png")},
        data={
            "deskew": "false",
            "normalize": "false",
            "auto_grid": "true",
            "rpeaks_lead": "II",
            "rpeaks_robust": "false",
            "intervals": "false",
        },
    )

    assert response.status_code == 200
    data = response.json()

    report = data["report"]

    # Should have capabilities even if CV modules fail
    assert "capabilities" in report
    assert isinstance(report["capabilities"], list)

    # May have segmentation capability if CV modules work
    capabilities = report["capabilities"]
    if "segmentation" in capabilities:
        # If segmentation works, check structure
        assert "segmentation" in report

    # Should have flags indicating processing status
    assert "flags" in report
    assert isinstance(report["flags"], list)


def test_file_size_validation():
    """Test file size limit validation."""
    # Create a large dummy file (larger than 8MB default limit)
    large_data = b"x" * (9 * 1024 * 1024)  # 9MB

    response = client.post(
        "/ecg/process-inline",
        files={"file": ("large.png", large_data, "image/png")},
        data={"deskew": "false"},
    )

    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()


def test_unsupported_file_type():
    """Test unsupported file type validation."""
    text_data = b"This is not an image"

    response = client.post(
        "/ecg/process-inline",
        files={"file": ("test.txt", text_data, "text/plain")},
        data={"deskew": "false"},
    )

    assert response.status_code == 415
    assert "unsupported" in response.json()["detail"].lower()


def test_compact_response():
    """Test compact response option."""
    image_data = create_test_image()

    response = client.post(
        "/ecg/process-inline?compact=true",
        files={"file": ("test.png", image_data, "image/png")},
        data={"deskew": "false"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should have summary but not full report in compact mode
    assert "summary" in data
    assert "report" not in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
