# intelligence/service/app/config/settings.py
"""Composite settings combining all configuration domains (Composition pattern)."""

from app.config.app_config import AppConfig
from app.config.intelligence_config import IntelligenceConfig
from app.config.provider_config import ProviderConfig
from app.config.observability_config import ObservabilityConfig


class Settings(AppConfig, IntelligenceConfig, ProviderConfig, ObservabilityConfig):
    """
    Composite Settings class combining all configuration domains.
    
    Follows composition pattern for SOLID principles and easier testing.
    Each domain can be configured independently and tested in isolation.
    """
    pass


# Global settings instance
_settings: Settings = None


def get_settings() -> Settings:
    """Get or create global settings instance.
    
    Returns:
        Settings instance
    """
    global _settings
    
    if _settings is None:
        _settings = Settings()
    
    return _settings
