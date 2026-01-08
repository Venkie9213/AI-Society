# tests/conftest.py
"""Pytest configuration and fixtures"""

import pytest
import asyncio
from typing import AsyncGenerator
import os

# Set test environment
os.environ["DEBUG"] = "true"
os.environ["DATABASE_URL"] = "postgresql://intelligence:dev_password@localhost:5432/intelligence_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_gemini_response():
    """Mock Gemini response using new Client syntax"""
    class MockUsageMetadata:
        input_token_count = 10
        output_token_count = 5
    
    class MockCandidate:
        class FinishReason:
            name = "STOP"
        
        finish_reason = FinishReason()
    
    class MockResponse:
        text = "Test response"
        usage_metadata = MockUsageMetadata()
        candidates = [MockCandidate()]
    
    return MockResponse()


@pytest.fixture
def provider_config():
    """Provide test provider configuration using new unified SDK"""
    return {
        "primary_provider": "gemini",
        "fallback_providers": ["gemini"],
        "provider_configs": {
            "gemini": {
                "api_key": "test-key",
                "model": "gemini-2.5-flash",
                "temperature": 0.7,
                "max_tokens": 1000,
                "timeout_seconds": 30,
            }
        }
    }


@pytest.fixture
def llm_message():
    """Provide test LLM message"""
    from app.providers.base import LLMMessage
    return LLMMessage(role="user", content="Test message")


@pytest.fixture
def llm_messages():
    """Provide test LLM messages"""
    from app.providers.base import LLMMessage
    return [
        LLMMessage(role="system", content="You are helpful"),
        LLMMessage(role="user", content="Hello"),
    ]
