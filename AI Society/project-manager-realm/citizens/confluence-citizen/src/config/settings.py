from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # App Settings
    app_name: str = "Confluence Citizen"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    
    # Kafka Settings
    kafka_brokers: str = "localhost:9092"
    kafka_consumer_group: str = "confluence-citizen-group"
    kafka_topic_prd_generated: str = "project-manager.requirement.prd.generated"
    
    # Confluence Settings
    confluence_url: str = "https://your-domain.atlassian.net"
    confluence_username: str = "user@example.com"
    confluence_api_token: str = ""
    confluence_default_space: str = "~"  # Default to user space
    
    # Workspace Council
    workspace_council_url: str = "http://workspace-council:8000"
    
    # Metrics
    metrics_port: int = 9001
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
