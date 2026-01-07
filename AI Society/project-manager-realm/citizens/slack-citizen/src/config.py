"""Configuration management for Slack Citizen service."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Slack Configuration
    slack_signing_secret: str = Field(
        ...,
        description="Slack signing secret for webhook verification",
        env=("PRODUCT_MANAGER_SLACK_SIGNING_SECRET", "SLACK_SIGNING_SECRET"),
    )
    slack_bot_token: str = Field(
        ...,
        description="Slack bot OAuth token for API calls",
        env=("PRODUCT_MANAGER_SLACK_BOT_TOKEN", "SLACK_BOT_TOKEN"),
    )

    # Kafka Configuration
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Comma-separated list of Kafka broker addresses",
    )
    kafka_topic_prefix: str = Field(
        default="project-manager",
        description="Prefix for all Kafka topics",
    )
    kafka_consumer_group_id: str = Field(
        default="slack-citizen-consumer",
        description="Kafka consumer group ID",
    )
    kafka_auto_create_topics: bool = Field(
        default=True,
        description="Automatically create Kafka topics if they don't exist",
    )

    # Multi-tenancy Configuration
    tenant_mapping_service_url: str = Field(
        default="http://localhost:8080/api/tenants",
        description="URL of the tenant mapping service",
    )
    default_tenant_id: str = Field(
        default="default",
        description="Default tenant ID for unmapped Slack workspaces",
    )

    # Application Configuration
    app_name: str = Field(
        default="slack-citizen",
        description="Application name",
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version",
    )
    app_port: int = Field(
        default=8000,
        description="Port to run the application on",
    )
    environment: str = Field(
        default="development",
        description="Environment name (development, staging, production)",
    )

    # Observability Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    jaeger_agent_host: str = Field(
        default="localhost",
        description="Jaeger agent host for distributed tracing",
    )
    jaeger_agent_port: int = Field(
        default=6831,
        description="Jaeger agent port",
    )
    prometheus_port: int = Field(
        default=9090,
        description="Port for Prometheus metrics endpoint",
    )
    enable_tracing: bool = Field(
        default=True,
        description="Enable distributed tracing",
    )
    enable_metrics: bool = Field(
        default=True,
        description="Enable Prometheus metrics",
    )

    # Retry Configuration
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

    # Rate Limiting Configuration
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting",
    )
    rate_limit_requests_per_minute: int = Field(
        default=60,
        description="Maximum requests per minute per tenant",
    )

    @property
    def kafka_servers_list(self) -> list[str]:
        """Parse Kafka bootstrap servers into a list."""
        return [s.strip() for s in self.kafka_bootstrap_servers.split(",")]

    def get_kafka_topic(self, topic_name: str) -> str:
        """Generate full Kafka topic name with prefix."""
        return f"{self.kafka_topic_prefix}.{topic_name}"

    def get_dlq_topic(self, original_topic: str) -> str:
        """Generate Dead Letter Queue topic name."""
        return f"{original_topic}{self.dlq_topic_suffix}"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


# Global settings instance
settings = Settings()
