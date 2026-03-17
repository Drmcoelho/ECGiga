"""Tests for the MCP server endpoints."""

import json
import math
import pytest
from fastapi.testclient import TestClient
from mcp_server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_sse_endpoint(client):
    resp = client.get("/sse")
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")


def test_catalog(client):
    resp = client.get("/catalog")
    assert resp.status_code == 200
    data = resp.json()
    assert "tools" in data
    tool_names = [t["name"] for t in data["tools"]]
    assert "quiz_validate" in tool_names
    assert "analyze_intervals" in tool_names
    assert "ecg_image_process" in tool_names
    assert "ecg_interpret" in tool_names
    assert "quiz_adaptive" in tool_names


def test_analyze_intervals_normal(client):
    resp = client.post(
        "/analyze_intervals",
        json={"pr_ms": 160, "qrs_ms": 90, "qt_ms": 380, "rr_ms": 800},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "qtc_ms" in data
    assert "flags" in data
    assert "explanation" in data
    # QTc should be reasonable
    assert 300 < data["qtc_ms"] < 600
    # Normal intervals should have no flags
    assert len(data["flags"]) == 0


def test_analyze_intervals_invalid_rr(client):
    resp = client.post(
        "/analyze_intervals",
        json={"pr_ms": 160, "qrs_ms": 90, "qt_ms": 380, "rr_ms": 0},
    )
    assert resp.status_code == 422

    resp = client.post(
        "/analyze_intervals",
        json={"pr_ms": 160, "qrs_ms": 90, "qt_ms": 380, "rr_ms": -100},
    )
    assert resp.status_code == 422


def test_analyze_intervals_prolonged_pr(client):
    resp = client.post(
        "/analyze_intervals",
        json={"pr_ms": 220, "qrs_ms": 90, "qt_ms": 380, "rr_ms": 800},
    )
    data = resp.json()
    assert any("BAV" in f or "PR > 200" in f for f in data["flags"])


def test_analyze_intervals_wide_qrs(client):
    resp = client.post(
        "/analyze_intervals",
        json={"pr_ms": 160, "qrs_ms": 130, "qt_ms": 380, "rr_ms": 800},
    )
    data = resp.json()
    assert any("QRS" in f and "120" in f for f in data["flags"])


def test_analyze_intervals_prolonged_qtc(client):
    resp = client.post(
        "/analyze_intervals",
        json={"pr_ms": 160, "qrs_ms": 90, "qt_ms": 500, "rr_ms": 600},
    )
    data = resp.json()
    assert any("QTc" in f and "prolongado" in f for f in data["flags"])


def test_analyze_intervals_rejects_nonpositive_rr(client):
    resp = client.post(
        "/analyze_intervals",
        json={"pr_ms": 160, "qrs_ms": 90, "qt_ms": 380, "rr_ms": 0},
    )
    assert resp.status_code == 422


def test_quiz_validate_valid_file(client, sample_quiz_path):
    resp = client.post("/quiz_validate", json={"path": sample_quiz_path})
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert len(data["errors"]) == 0


def test_quiz_validate_nonexistent(client):
    resp = client.post("/quiz_validate", json={"path": "/nonexistent/file.json"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False
    assert len(data["errors"]) > 0


def test_quiz_validate_rejects_localhost_url(client):
    resp = client.post("/quiz_validate", json={"path": "http://127.0.0.1/test.json"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False
    assert any("not allowed" in err for err in data["errors"])


def test_ecg_image_process_rejects_localhost_url(client):
    resp = client.post("/ecg_image_process", json={"image_url": "http://localhost/ecg.png", "ops": ["grid"]})
    assert resp.status_code == 200
    data = resp.json()
    assert any("not allowed" in flag for flag in data["report"]["flags"])
