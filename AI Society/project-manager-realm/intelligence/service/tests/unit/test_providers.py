# tests/unit/test_providers.py
"""Unit tests for LLM providers"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from app.providers.base import LLMProvider, LLMMessage, LLMResponse
from app.providers.gemini import GeminiProvider, GEMINI_PRICING
from app.providers.router import ProviderRouter


class TestLLMMessage:
    """Test LLMMessage dataclass"""
    
    def test_message_creation(self):
        """Test creating a message"""
        msg = LLMMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"


class TestLLMResponse:
    """Test LLMResponse dataclass"""
    
    def test_response_creation(self):
        """Test creating a response"""
        response = LLMResponse(
            content="Hello",
            model="gemini-1.5-flash",
            prompt_tokens=10,
            completion_tokens=5,
            cost_cents=0.1,
        )
        assert response.content == "Hello"
        assert response.model == "gemini-1.5-flash"
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 5


class TestGeminiProvider:
    """Test Gemini provider"""
    
    def test_provider_initialization(self):
        """Test Gemini provider initialization with new Client SDK"""
        config = {
            "api_key": "test-key",
            "model": "gemini-2.5-flash",
            "temperature": 0.7,
            "max_tokens": 1000,
        }
        
        provider = GeminiProvider(config)
        assert provider.model == "gemini-2.5-flash"
        assert provider.temperature == 0.7
        assert provider.max_tokens == 1000
    
    def test_provider_initialization_no_api_key(self):
        """Test initialization without API key"""
        config = {
            "model": "gemini-1.5-flash",
        }
        
        provider = GeminiProvider(config)
        assert provider.client is None
    
    def test_cost_calculation(self):
        """Test cost calculation for Gemini 2.5 Flash"""
        config = {
            "api_key": "test-key",
            "model": "gemini-2.5-flash",
        }
        
        provider = GeminiProvider(config)
        
        # Test cost calculation
        # gemini-2.5-flash: $0.075/1M input, $0.30/1M output
        # 1000 input tokens = 0.075/1000 = 0.000075 USD = 0.0075 cents
        # 500 output tokens = 0.30/1000 = 0.00015 USD = 0.015 cents
        # Total = 0.0225 cents
        cost = provider._calculate_cost(1000, 500)
        expected_cost = (1000 * 0.075 / 1_000_000) + (500 * 0.30 / 1_000_000)
        assert abs(cost - expected_cost) < 0.0001
    
    def test_message_conversion(self):
        """Test message conversion to Gemini format"""
        messages = [
            LLMMessage(role="system", content="You are helpful"),
            LLMMessage(role="user", content="Hello"),
            LLMMessage(role="assistant", content="Hi there"),
        ]
        
        result = GeminiProvider._convert_messages(messages)
        
        assert "[SYSTEM]:" in result
        assert "[USER]:" in result
        assert "[ASSISTANT]:" in result
        assert "You are helpful" in result
        assert "Hello" in result
        assert "Hi there" in result
    
    @pytest.mark.asyncio
    async def test_health_check_no_client(self):
        """Test health check without client"""
        config = {"model": "gemini-1.5-flash"}
        provider = GeminiProvider(config)
        
        is_healthy = await provider.health_check()
        assert is_healthy is False


class TestProviderRouter:
    """Test provider router"""
    
    def test_router_initialization(self):
        """Test router initialization"""
        config = {
            "primary_provider": "gemini",
            "fallback_providers": ["gemini"],
            "provider_configs": {
                "gemini": {
                    "api_key": "test-key",
                    "model": "gemini-1.5-flash",
                }
            }
        }
        
        router = ProviderRouter(config)
        assert router.primary_provider == "gemini"
        assert "gemini" in router.list_providers()
    
    def test_router_get_provider(self):
        """Test getting a provider"""
        config = {
            "primary_provider": "gemini",
            "fallback_providers": ["gemini"],
            "provider_configs": {
                "gemini": {
                    "api_key": "test-key",
                    "model": "gemini-1.5-flash",
                }
            }
        }
        
        router = ProviderRouter(config)
        provider = router.get_provider("gemini")
        assert provider is not None
        assert provider.model == "gemini-1.5-flash"
    
    def test_router_list_providers(self):
        """Test listing providers"""
        config = {
            "primary_provider": "gemini",
            "fallback_providers": ["gemini"],
            "provider_configs": {
                "gemini": {
                    "api_key": "test-key",
                    "model": "gemini-1.5-flash",
                }
            }
        }
        
        router = ProviderRouter(config)
        providers = router.list_providers()
        assert "gemini" in providers
    
    @pytest.mark.asyncio
    async def test_router_health_check(self):
        """Test health check"""
        config = {
            "primary_provider": "gemini",
            "fallback_providers": ["gemini"],
            "provider_configs": {
                "gemini": {
                    "api_key": "test-key",
                    "model": "gemini-1.5-flash",
                }
            }
        }
        
        router = ProviderRouter(config)
        health_status = await router.health_check()
        
        assert isinstance(health_status, dict)
        assert "gemini" in health_status


class TestGeminiPricing:
    """Test Gemini pricing constants"""
    
    def test_pricing_constants_exist(self):
        """Test that pricing constants are defined for all models"""
        assert "gemini-3-flash-preview" in GEMINI_PRICING
        assert "gemini-2.5-flash" in GEMINI_PRICING
        assert "gemini-2.5-flash-lite" in GEMINI_PRICING
        assert "gemini-1.5-flash" in GEMINI_PRICING
        assert "gemini-1.5-pro" in GEMINI_PRICING
    
    def test_flash_lite_is_cheapest(self):
        """Test that Flash Lite is the cheapest model"""
        lite_input = GEMINI_PRICING["gemini-2.5-flash-lite"]["input"]
        flash_input = GEMINI_PRICING["gemini-2.5-flash"]["input"]
        
        assert lite_input < flash_input
    
    def test_pricing_has_input_output(self):
        """Test that pricing has input and output costs"""
        for model, pricing in GEMINI_PRICING.items():
            assert "input" in pricing
            assert "output" in pricing
            assert pricing["input"] > 0
            assert pricing["output"] > 0
    
    def test_flash_pricing_is_cheapest(self):
        """Test that Flash is cheaper than Pro models"""
        flash_input = GEMINI_PRICING["gemini-2.5-flash"]["input"]
        pro_input = GEMINI_PRICING["gemini-2.5-pro"]["input"]
        
        assert flash_input < pro_input
