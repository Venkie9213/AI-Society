"""Retry and resilience configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RetryConfig(BaseSettings):
    """Retry strategy and Dead Letter Queue configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    max_retry_attempts: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed operations",
    )
    retry_base_delay_seconds: float = Field(
        default=1.0,
        description="Base delay in seconds for exponential backoff",
    )
    retry_max_delay_seconds: float = Field(
        default=60.0,
        description="Maximum delay in seconds for exponential backoff",
    )
    dlq_topic_suffix: str = Field(
        default=".dlq",
        description="Suffix for Dead Letter Queue topics",
    )

    def get_dlq_topic(self, original_topic: str) -> str:
        """Generate Dead Letter Queue topic name."""
        return f"{original_topic}{self.dlq_topic_suffix}"
