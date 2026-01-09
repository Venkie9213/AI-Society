# app/api/providers.py
"""Provider management endpoints"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from app.providers.manager import get_provider_router, health_check as provider_health_check
import structlog

logger = structlog.get_logger()

router = APIRouter()


@router.get("/providers")
async def list_providers() -> Dict[str, Any]:
    """List available LLM providers
    
    Returns:
        List of available providers with their status
    """
    try:
        provider_router = get_provider_router()
        available_providers = provider_router.list_providers()
        health_status = await provider_router.health_check()
        
        providers_info = []
        for provider_name in available_providers:
            provider_instance = provider_router.get_provider(provider_name)
            providers_info.append({
                "name": provider_name,
                "healthy": health_status.get(provider_name, False),
                "model": provider_instance.model if provider_instance else None,
            })
        
        return {
            "providers": providers_info,
            "primary": provider_router.primary_provider,
            "fallbacks": [p for p in provider_router.fallback_providers if p != provider_router.primary_provider],
        }
    except Exception as e:
        logger.error("list_providers_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/health")
async def providers_health() -> Dict[str, bool]:
    """Check health of all providers
    
    Returns:
        Dictionary mapping provider names to health status
    """
    try:
        return await provider_health_check()
    except Exception as e:
        logger.error("providers_health_check_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/providers/test")
async def test_provider(provider: str = "gemini", prompt: str = "Say 'test successful'") -> Dict[str, Any]:
    """Test a specific provider with a prompt
    
    Args:
        provider: Provider name to test
        prompt: Test prompt
        
    Returns:
        Response from provider
    """
    try:
        from app.providers.base import LLMMessage
        
        provider_router = get_provider_router()
        provider_instance = provider_router.get_provider(provider)
        
        if not provider_instance:
            raise HTTPException(status_code=404, detail=f"Provider {provider} not found")
        
        # Test with simple message
        messages = [LLMMessage(role="user", content=prompt)]
        response = await provider_instance.generate(messages)
        
        return {
            "provider": provider,
            "content": response.content,
            "tokens": {
                "prompt": response.prompt_tokens,
                "completion": response.completion_tokens,
            },
            "cost_cents": response.cost_cents,
        }
    except Exception as e:
        logger.error("test_provider_failed", provider=provider, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
