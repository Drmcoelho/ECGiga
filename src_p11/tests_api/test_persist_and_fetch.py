"""
Test persistence and report retrieval functionality.

Tests storing reports with persist=true and retrieving them via /reports endpoints.
"""

import io
import os
import shutil
import sys
import tempfile
from pathlib import Path

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

    # Draw some simple lines to mimic ECG trace
    for x in range(0, width, 10):
        y = height // 2 + (x % 50 - 25)
        draw.point((x, y), fill="black")

    img_buffer = io.BytesIO()
    img.save(img_buffer, format=format)
    img_buffer.seek(0)
    return img_buffer.getvalue()


@pytest.fixture
def temp_storage(monkeypatch):
    """Create temporary storage directory for testing."""
    temp_dir = tempfile.mkdtemp()

    # Mock the get_storage_root function to use temp directory
    def mock_get_storage_root():
        return temp_dir

    monkeypatch.setattr("api.dependencies.get_storage_root", lambda: Path(temp_dir))

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_persist_and_fetch_report(temp_storage):
    """Test storing and retrieving a report."""
    image_data = create_test_image()

    # First, ingest with persistence enabled
    response = client.post(
        "/ecg/process-inline?persist=true",
        files={"file": ("test.png", image_data, "image/png")},
        data={"deskew": "false", "normalize": "false", "auto_grid": "false"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should have report_id in response
    assert "report_id" in data
    assert "message" in data
    assert "saved successfully" in data["message"].lower()

    report_id = data["report_id"]
    assert isinstance(report_id, str)
    assert len(report_id) > 0

    # Now fetch the report
    fetch_response = client.get(f"/reports/{report_id}")
    assert fetch_response.status_code == 200

    fetched_report = fetch_response.json()

    # Should be identical to original report (plus report_id)
    original_report = data["report"]

    # Remove report_id from fetched for comparison
    fetched_without_id = fetched_report.copy()
    if "report_id" in fetched_without_id:
        del fetched_without_id["report_id"]

    # Key fields should match
    assert fetched_without_id["version"] == original_report["version"]
    assert fetched_without_id["capabilities"] == original_report["capabilities"]
    assert "meta" in fetched_without_id
    assert "measures" in fetched_without_id


def test_list_reports(temp_storage):
    """Test listing stored reports."""
    # Initially should be empty
    response = client.get("/reports/list")
    assert response.status_code == 200
    data = response.json()
    assert "reports" in data
    assert "pagination" in data
    assert len(data["reports"]) == 0
    assert data["pagination"]["total"] == 0

    # Store a few reports
    image_data = create_test_image()

    stored_ids = []
    for i in range(3):
        response = client.post(
            "/ecg/process-inline?persist=true",
            files={"file": (f"test_{i}.png", image_data, "image/png")},
            data={"deskew": "false"},
        )
        assert response.status_code == 200
        stored_ids.append(response.json()["report_id"])

    # Now list should show reports
    response = client.get("/reports/list")
    assert response.status_code == 200
    data = response.json()

    assert len(data["reports"]) == 3
    assert data["pagination"]["total"] == 3
    assert data["pagination"]["has_more"] == False

    # Check report metadata structure
    for report_meta in data["reports"]:
        assert "id" in report_meta
        assert "created_at" in report_meta
        assert "capabilities" in report_meta
        assert report_meta["id"] in stored_ids


def test_list_reports_pagination(temp_storage):
    """Test pagination in reports listing."""
    # Store several reports
    image_data = create_test_image()

    for i in range(5):
        response = client.post(
            "/ecg/process-inline?persist=true",
            files={"file": (f"test_{i}.png", image_data, "image/png")},
            data={"deskew": "false"},
        )
        assert response.status_code == 200

    # Test pagination
    response = client.get("/reports/list?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()

    assert len(data["reports"]) == 2
    assert data["pagination"]["total"] == 5
    assert data["pagination"]["has_more"] == True
    assert data["pagination"]["limit"] == 2
    assert data["pagination"]["offset"] == 0

    # Get next page
    response = client.get("/reports/list?limit=2&offset=2")
    assert response.status_code == 200
    data = response.json()

    assert len(data["reports"]) == 2
    assert data["pagination"]["total"] == 5
    assert data["pagination"]["has_more"] == True


def test_fetch_nonexistent_report():
    """Test fetching a report that doesn't exist."""
    fake_id = "nonexistent12345"

    response = client.get(f"/reports/{fake_id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_persist_compact_response(temp_storage):
    """Test persistence with compact response."""
    image_data = create_test_image()

    response = client.post(
        "/ecg/process-inline?persist=true&compact=true",
        files={"file": ("test.png", image_data, "image/png")},
        data={"deskew": "false"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should have report_id and summary, but not full report
    assert "report_id" in data
    assert "summary" in data
    assert "report" not in data

    # But should still be able to fetch the full report
    report_id = data["report_id"]
    fetch_response = client.get(f"/reports/{report_id}")
    assert fetch_response.status_code == 200

    full_report = fetch_response.json()
    assert "version" in full_report
    assert "capabilities" in full_report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
