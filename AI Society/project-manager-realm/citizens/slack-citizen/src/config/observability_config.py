"""Observability and monitoring configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ObservabilityConfig(BaseSettings):
    """Logging, tracing, and metrics configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

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
