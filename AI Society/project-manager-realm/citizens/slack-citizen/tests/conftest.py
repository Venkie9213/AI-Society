"""Test configuration."""

import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Reset environment variables for each test."""
    # Set test environment variables
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("PROJECT_MANAGER_SLACK_SIGNING_SECRET", "test_secret")
    monkeypatch.setenv("PROJECT_MANAGER_PROJECT_MANAGER_SLACK_BOT_TOKEN", "xoxb-test-token")
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
