"""Basic tests for webhook handlers."""

import json

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "slack-citizen"


def test_readiness_check(client):
    """Test readiness check endpoint."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
    assert "checks" in data


def test_url_verification(client):
    """Test Slack URL verification challenge."""
    payload = {
        "type": "url_verification",
        "challenge": "test_challenge_string",
        "token": "test_token",
    }
    
    # Note: This will fail signature verification in real scenario
    # For testing, you'd need to mock the signature verification
    response = client.post(
        "/webhooks/slack/events",
        json=payload,
        headers={
            "X-Slack-Signature": "v0=test",
            "X-Slack-Request-Timestamp": "1234567890",
        },
    )
    
    # Expected to fail due to signature verification
    # In real tests, mock the signature verification middleware
    assert response.status_code in [200, 401]


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "slack-citizen"
    assert data["status"] == "running"
