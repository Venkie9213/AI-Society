# intelligence/service/app/config/__init__.py
"""Configuration module - single consolidated AppConfig."""

from app.config.settings import Settings, get_settings
from app.config.app_config import AppConfig

__all__ = ["Settings", "get_settings", "AppConfig"]
