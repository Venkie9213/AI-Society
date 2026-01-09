"""LLM provider configuration."""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class LLMConfig(BaseSettings):
    """LLM provider configuration."""
    
    # Gemini Configuration (new unified SDK)
    gemini_api_key: str = Field(default="", description="Google Gemini API Key")
    gemini_model: str = Field(
        default="gemini-3-flash-preview",
        description="Gemini model version (default 3 Flash Preview - 2026)",
    )
    
    # Claude Configuration (for future use)
    claude_api_key: str = Field(default="", description="Anthropic Claude API Key")
    claude_model: str = Field(default="claude-3.5-sonnet", description="Claude model version")
    
    # OpenAI Configuration (for future use)
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    openai_model: str = Field(default="gpt-4-turbo-preview", description="GPT model version")
    
    # LLM Behavior
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1000, gt=0)
    timeout_seconds: int = Field(default=30, gt=0)
    retry_attempts: int = Field(default=3, ge=1)
    retry_delay: float = Field(default=1.0, gt=0)
    
    # Provider Strategy
    primary_provider: str = Field(
        default="gemini",
        description="Primary LLM provider (gemini, claude, gpt4)",
    )
    fallback_providers: List[str] = Field(
        default=["gemini"],
        description="Fallback providers in order",
    )
    
    # Development Mode
    development_mode: bool = Field(default=True)
    mock_llm_responses: bool = Field(default=False)
    
    class Config:
        env_file = ".env"
        case_sensitive = False
