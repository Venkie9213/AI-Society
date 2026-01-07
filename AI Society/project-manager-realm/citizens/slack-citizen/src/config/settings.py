"""Composite settings class combining all configuration domains."""

from src.config.app_config import AppConfig
from src.config.kafka_config import KafkaConfig
from src.config.observability_config import ObservabilityConfig
from src.config.rate_limit_config import RateLimitConfig
from src.config.retry_config import RetryConfig
from src.config.slack_config import SlackConfig
from src.config.tenancy_config import TenancyConfig


class Settings(
    AppConfig,
    SlackConfig,
    KafkaConfig,
    TenancyConfig,
    ObservabilityConfig,
    RetryConfig,
    RateLimitConfig,
):
    """
    Composite settings class combining all configuration domains.

    Follows the composition pattern for SOLID compliance.
    """

    pass


# Global settings instance
settings = Settings()
