"""Test configuration and fixtures for API tests."""
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)