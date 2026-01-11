from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "gateway_council"
    app_version: str = "0.1.0"
    
    # Workspace Council URL for tenant resolution
    workspace_council_url: str = "http://workspace-council:8000"
    
    # Service Routing
    slack_citizen_url: str = "http://slack-citizen:8000"
    confluence_citizen_url: str = "http://confluence-citizen:8000"
    
    # Secret for Slack signature verification
    project_manager_slack_signing_secret: str = "placeholder_secret"
    
    # Redis configuration for discovery
    redis_host: str = "shared-redis"
    redis_port: int = 6379
    
    class Config:
        env_file = ".env"

settings = Settings()
