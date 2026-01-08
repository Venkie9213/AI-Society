# app/providers/manager.py
"""Provider Manager - Global provider router instance"""

from typing import Optional
import structlog

from app.providers.router import ProviderRouter
from app.config import get_provider_config

logger = structlog.get_logger()

# Global provider router instance
_provider_router: Optional[ProviderRouter] = None


def init_provider_router() -> ProviderRouter:
    """Initialize global provider router
    
    Returns:
        ProviderRouter instance
    """
    global _provider_router
    
    if _provider_router is not None:
        return _provider_router
    
    config = get_provider_config()
    _provider_router = ProviderRouter(config)
    
    logger.info(
        "provider_manager_initialized",
        providers=_provider_router.list_providers(),
    )
    
    return _provider_router


def get_provider_router() -> ProviderRouter:
    """Get global provider router
    
    Returns:
        ProviderRouter instance
        
    Raises:
        RuntimeError: If router not initialized
    """
    if _provider_router is None:
        raise RuntimeError("Provider router not initialized. Call init_provider_router() first.")
    
    return _provider_router


async def health_check() -> dict:
    """Get health status of all providers
    
    Returns:
        Dictionary with provider health status
    """
    try:
        router = get_provider_router()
        return await router.health_check()
    except Exception as e:
        logger.error("provider_health_check_error", error=str(e))
        return {}
