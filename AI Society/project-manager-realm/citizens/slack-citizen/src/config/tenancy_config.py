"""Multi-tenancy configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TenancyConfig(BaseSettings):
    """Multi-tenancy and tenant mapping configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    tenant_mapping_service_url: str = Field(
        default="http://localhost:8080/api/tenants",
        description="URL of the tenant mapping service",
    )
    default_tenant_id: str = Field(
        default="default",
        description="Default tenant ID for unmapped Slack workspaces",
    )
