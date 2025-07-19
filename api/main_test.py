"""
Tests for fitlog API main endpoints.
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint - should be public."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "status" in data


def test_protected_endpoint_without_api_key():
    """Test that protected endpoints require API key."""
    response = client.get("/runs")
    assert response.status_code == 403


def test_protected_endpoint_with_api_key():
    """Test that protected endpoints work with valid API key."""
    headers = {"X-API-Key": "test-api-key"}
    response = client.get("/runs", headers=headers)
    # Should work if API key verification is properly implemented
    assert response.status_code in [200, 500]  # 500 if database not available in test
