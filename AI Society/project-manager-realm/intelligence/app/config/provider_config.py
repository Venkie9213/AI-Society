# intelligence/service/app/config/provider_config.py
"""LLM Provider configuration (API keys, endpoints, settings)."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class ProviderConfig(BaseSettings):
    """LLM provider configuration."""
    pass  # All fields now in AppConfig


_provider_config: Optional[ProviderConfig] = None


def get_provider_config() -> ProviderConfig:
    """Get or create provider config singleton.
    
    Returns:
        ProviderConfig instance
    """
    global _provider_config
    if _provider_config is None:
        _provider_config = ProviderConfig()
    return _provider_config
