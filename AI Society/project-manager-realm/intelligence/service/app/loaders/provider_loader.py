# intelligence/service/app/loaders/provider_loader.py
"""Provider configuration loader - loads from models/providers.yaml."""

from typing import Dict, Any, Optional
from pathlib import Path
import yaml
import structlog

from app.loaders.base_loader import BaseLoader
from app.config import Settings

logger = structlog.get_logger()


class ProviderLoader(BaseLoader):
    """Loads LLM provider configurations."""
    
    def __init__(self, settings: Settings, cache_enabled: bool = True):
        """Initialize provider loader.
        
        Args:
            settings: Application settings
            cache_enabled: Whether to enable caching
        """
        super().__init__(cache_enabled=cache_enabled)
        self.settings = settings
        self.providers_file = settings.models_path / "providers.yaml"
    
    def load_providers(self) -> Dict[str, Any]:
        """Load provider configurations.
        
        Returns:
            Provider configuration dictionary
        """
        cached = self._get_cached("providers")
        if cached is not None:
            return cached
        
        if not self.providers_file.exists():
            logger.warning("providers_file_not_found", path=str(self.providers_file))
            return self._get_default_providers()
        
        try:
            with open(self.providers_file, "r") as f:
                config = yaml.safe_load(f)
            
            logger.info("providers_loaded", path=str(self.providers_file))
            self._set_cache("providers", config)
            return config
            
        except Exception as e:
            logger.error("providers_load_failed", error=str(e))
            return self._get_default_providers()
    
    def get_provider_config(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get specific provider configuration.
        
        Args:
            provider_id: Provider identifier (e.g., "gemini")
            
        Returns:
            Provider configuration or None
        """
        providers = self.load_providers()
        
        for provider in providers.get("providers", []):
            if provider.get("id") == provider_id:
                return provider
        
        logger.warning("provider_not_found", provider_id=provider_id)
        return None
    
    def get_model_config(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get specific model configuration across all providers.
        
        Args:
            model_id: Model identifier (e.g., "gemini-3-flash-preview")
            
        Returns:
            Model configuration or None
        """
        providers = self.load_providers()
        
        for provider in providers.get("providers", []):
            for model in provider.get("models", []):
                if model.get("id") == model_id:
                    return model
        
        logger.warning("model_not_found", model_id=model_id)
        return None
    
    def get_routing_config(self) -> Optional[Dict[str, Any]]:
        """Get routing configuration.
        
        Returns:
            Routing configuration or None
        """
        providers = self.load_providers()
        return providers.get("routing")
    
    def get_provider_for_use_case(self, use_case: str) -> Optional[str]:
        """Get recommended model for use case.
        
        Args:
            use_case: Use case name (e.g., "reasoning", "budget", "production")
            
        Returns:
            Model ID or None
        """
        routing = self.get_routing_config()
        if not routing:
            return None
        
        use_cases = routing.get("use_cases", {})
        models = use_cases.get(use_case)
        
        if models and isinstance(models, list):
            return models[0]  # Return first (primary) model
        
        logger.warning("use_case_not_found", use_case=use_case)
        return None
    
    def _get_default_providers(self) -> Dict[str, Any]:
        """Get default provider configuration as fallback.
        
        Returns:
            Default provider configuration
        """
        return {
            "providers": [
                {
                    "id": "gemini",
                    "name": "Google Gemini",
                    "models": [
                        {
                            "id": "gemini-3-flash-preview",
                            "name": "Gemini 3 Flash Preview (Default)",
                            "pricing": {
                                "input_per_1m": 0.50,
                                "output_per_1m": 3.00,
                            },
                            "rate_limits": {
                                "rpm": 10,
                                "tpm": 100000,
                            },
                        }
                    ],
                }
            ],
            "routing": {
                "primary_chain": ["gemini-3-flash-preview"],
                "use_cases": {
                    "reasoning": ["gemini-3-pro-preview"],
                    "budget": ["gemini-2.5-flash-lite"],
                    "production": ["gemini-3-flash-preview"],
                },
            },
        }


# Global provider loader instance
_provider_loader: Optional[ProviderLoader] = None


def get_provider_loader(settings: Optional[Settings] = None) -> ProviderLoader:
    """Get or create global provider loader instance.
    
    Args:
        settings: Optional settings instance
        
    Returns:
        ProviderLoader instance
    """
    global _provider_loader
    
    if _provider_loader is None:
        from app.config import get_settings
        settings = settings or get_settings()
        _provider_loader = ProviderLoader(settings)
    
    return _provider_loader
