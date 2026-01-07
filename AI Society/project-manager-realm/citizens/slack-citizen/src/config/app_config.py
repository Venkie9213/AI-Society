"""Application runtime configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Application runtime and environment configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

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

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
