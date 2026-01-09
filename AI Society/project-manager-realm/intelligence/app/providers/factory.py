"""LLM Provider Factory - Creates provider instances with dependency injection.

Uses factory pattern to abstract provider creation and configuration.
"""

from typing import Dict, Any, Optional
import structlog

from app.providers.base import LLMProvider
from app.providers.implementations.gemini import GeminiProvider
from app.config import get_settings

logger = structlog.get_logger()


class ProviderFactory:
    """Factory for creating LLM provider instances.
    
    Supports:
    - Dynamic provider creation by name
    - Dependency injection of configuration
    - Provider caching
    - Fallback provider creation
    """
    
    # Supported provider types
    PROVIDERS = {
        "gemini": GeminiProvider,
    }
    
    def __init__(self):
        """Initialize provider factory."""
        self._instances: Dict[str, LLMProvider] = {}
        self.settings = get_settings()
    
    def create(
        self,
        provider_name: str,
        cache: bool = True,
    ) -> LLMProvider:
        """Create a provider instance.
        
        Args:
            provider_name: Name of provider (gemini, claude, etc.)
            cache: Whether to cache the instance
            
        Returns:
            LLMProvider instance
            
        Raises:
            ValueError: If provider not supported
        """
        # Return cached instance if available
        if cache and provider_name in self._instances:
            logger.debug("provider_instance_cached", provider=provider_name)
            return self._instances[provider_name]
        
        # Get provider class
        provider_class = self.PROVIDERS.get(provider_name)
        if provider_class is None:
            raise ValueError(f"Unsupported provider: {provider_name}")
        
        # Create configuration based on provider type
        config = self._build_config_for_provider(provider_name)
        
        # Create instance
        instance = provider_class(config)
        logger.info("provider_instance_created", provider=provider_name)
        
        # Cache if requested
        if cache:
            self._instances[provider_name] = instance
        
        return instance
    
    def _build_config_for_provider(self, provider_name: str) -> Dict[str, Any]:
        """Build configuration for a specific provider.
        
        Args:
            provider_name: Provider name
            
        Returns:
            Configuration dictionary
        """
        if provider_name == "gemini":
            return {
                "api_key": self.settings.gemini_api_key,
                "model": self.settings.gemini_model,
                "temperature": self.settings.temperature,
                "max_tokens": self.settings.max_tokens,
                "timeout_seconds": self.settings.timeout_seconds,
            }
        else:
            raise ValueError(f"Unknown provider: {provider_name}")
    
    def get_default_provider(self) -> LLMProvider:
        """Get the default configured provider.
        
        Returns:
            LLMProvider instance
        """
        return self.create(self.settings.primary_provider)
    
    def clear_cache(self) -> None:
        """Clear cached provider instances."""
        self._instances.clear()
        logger.info("provider_cache_cleared")


# Global factory instance
_factory: Optional[ProviderFactory] = None


def get_provider_factory() -> ProviderFactory:
    """Get or create global provider factory.
    
    Returns:
        ProviderFactory instance
    """
    global _factory
    if _factory is None:
        _factory = ProviderFactory()
    return _factory
