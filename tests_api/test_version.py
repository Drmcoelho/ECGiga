"""Tests for version endpoint."""
import pytest
from fastapi.testclient import TestClient

from api.main import app


def test_version_endpoint():
    """Test version endpoint returns correct JSON structure."""
    client = TestClient(app)
    
    response = client.get("/version")
    
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify required fields are present
    assert "app_version" in data
    assert "schema_supported" in data
    
    # Verify field types
    assert isinstance(data["app_version"], str)
    assert isinstance(data["schema_supported"], list)
    
    # Verify app_version is non-empty
    assert len(data["app_version"]) > 0
    
    # Verify schema_supported contains expected versions
    schema_versions = data["schema_supported"]
    assert len(schema_versions) > 0
    
    # All versions should be strings
    for version in schema_versions:
        assert isinstance(version, str)
    
    # Should include at least these specific versions as mentioned in problem statement
    expected_versions = ["0.4.0", "0.5.0"]
    for version in expected_versions:
        assert version in schema_versions


def test_version_endpoint_schema_format():
    """Test version endpoint schema_supported has correct format."""
    client = TestClient(app)
    
    response = client.get("/version")
    data = response.json()
    
    schema_versions = data["schema_supported"]
    
    # Each version should follow semantic versioning format
    import re
    version_pattern = re.compile(r'^\d+\.\d+\.\d+$')
    
    for version in schema_versions:
        assert version_pattern.match(version), f"Version {version} doesn't match semver format"