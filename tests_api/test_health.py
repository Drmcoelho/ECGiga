"""Tests for health endpoint."""
import pytest
from fastapi.testclient import TestClient

from api.main import app


def test_health_endpoint():
    """Test health endpoint returns correct JSON structure."""
    client = TestClient(app)
    
    response = client.get("/health")
    
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify required fields are present
    assert "status" in data
    assert "tesseract" in data
    assert "api_key_configured" in data
    
    # Verify field types
    assert isinstance(data["status"], str)
    assert isinstance(data["tesseract"], bool)
    assert isinstance(data["api_key_configured"], bool)
    
    # Verify status is "ok"
    assert data["status"] == "ok"


def test_health_endpoint_tesseract_field():
    """Test health endpoint includes tesseract availability."""
    client = TestClient(app)
    
    response = client.get("/health")
    data = response.json()
    
    # tesseract field should be boolean
    assert data["tesseract"] in [True, False]