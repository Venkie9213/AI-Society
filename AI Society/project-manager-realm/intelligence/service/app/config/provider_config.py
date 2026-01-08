# intelligence/service/app/config/provider_config.py
"""LLM Provider configuration (API keys, endpoints, settings)."""

import os
from typing import Optional
from pydantic import BaseSettings


class ProviderConfig(BaseSettings):
    """LLM provider configuration."""
    
    # Gemini
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
    gemini_endpoint: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_timeout_seconds: int = 60
    gemini_max_retries: int = 3
    
    # Claude (future)
    claude_api_key: Optional[str] = os.getenv("CLAUDE_API_KEY")
    claude_endpoint: str = "https://api.anthropic.com/v1"
    claude_timeout_seconds: int = 60
    claude_max_retries: int = 3
    
    # OpenAI (future)
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_endpoint: str = "https://api.openai.com/v1"
    openai_timeout_seconds: int = 60
    openai_max_retries: int = 3
    
    # Rate limiting
    enable_rate_limiting: bool = True
    rate_limit_check_interval_seconds: int = 60
    
    # Cost tracking
    track_costs: bool = True
    cost_currency: str = "USD"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
