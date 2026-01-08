# intelligence/service/app/config/intelligence_config.py
"""Intelligence Service configuration (agents, prompts, models)."""

import os
from pathlib import Path
from pydantic import BaseSettings


class IntelligenceConfig(BaseSettings):
    """Intelligence-specific configuration."""
    
    # Intelligence directory paths
    intelligence_root: Path = (
        Path(__file__).parent.parent.parent.parent / "intelligence"
    )
    models_path: Path = intelligence_root / "models"
    agents_path: Path = intelligence_root / "agents"
    prompts_path: Path = intelligence_root / "prompts"
    
    # Configuration cache
    cache_configs: bool = True
    config_cache_ttl_seconds: int = 3600  # 1 hour
    
    # Default routing
    default_provider: str = "gemini"
    default_model: str = "gemini-3-flash-preview"
    default_temperature: float = 0.7
    default_max_tokens: int = 1000
    
    # Fallback models (in priority order)
    fallback_models: list = [
        "gemini-3-flash-preview",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
