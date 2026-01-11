# intelligence/service/app/loaders/config_loader.py
"""Central configuration loader - orchestrates all loaders."""

from typing import Optional
import structlog

from app.config import Settings, get_settings
from app.loaders.implementations.provider_loader import ProviderLoader, get_provider_loader
from app.loaders.implementations.agent_loader import AgentLoader, get_agent_loader
from app.loaders.implementations.prompt_loader import PromptLoader, get_prompt_loader

logger = structlog.get_logger()


class ConfigLoader:
    """Central configuration loader orchestrating all loaders."""
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize config loader.
        
        Args:
            settings: Optional settings instance
        """
        self.settings = settings or get_settings()
        self.provider_loader = get_provider_loader(self.settings)
        self.agent_loader = get_agent_loader(self.settings)
        self.prompt_loader = get_prompt_loader(self.settings)
        
        logger.info("config_loader_initialized")
    
    def load_all_configs(self) -> None:
        """Load all configurations (useful for initialization)."""
        logger.info("loading_all_configs")
        self.provider_loader.load_providers()
        self.agent_loader.load_agents()
        self.prompt_loader.load_prompts()
        logger.info("all_configs_loaded")
    
    def clear_caches(self) -> None:
        """Clear all configuration caches."""
        logger.info("clearing_all_caches")
        self.provider_loader.clear_cache()
        self.agent_loader.clear_cache()
        self.prompt_loader.clear_cache()
        logger.info("all_caches_cleared")


# Global config loader instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader(settings: Optional[Settings] = None) -> ConfigLoader:
    """Get or create global config loader instance.
    
    Args:
        settings: Optional settings instance
        
    Returns:
        ConfigLoader instance
    """
    global _config_loader
    
    if _config_loader is None:
        settings = settings or get_settings()
        _config_loader = ConfigLoader(settings)
    
    return _config_loader
