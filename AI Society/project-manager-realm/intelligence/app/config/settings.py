# intelligence/service/app/config/settings.py
"""Composite settings - simplified to use AppConfig directly."""

from app.config.app_config import AppConfig


# Use AppConfig directly as Settings
Settings = AppConfig


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
