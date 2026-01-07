"""Rate limiting configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RateLimitConfig(BaseSettings):
    """Rate limiting configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting",
    )
    rate_limit_requests_per_minute: int = Field(
        default=60,
        description="Maximum requests per minute per tenant",
    )
