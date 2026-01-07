"""Slack API configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SlackConfig(BaseSettings):
    """Slack API configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

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
