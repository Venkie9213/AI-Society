from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # App Settings
    app_name: str = "Jira Citizen"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    
    # Kafka Settings
    kafka_brokers: str = "localhost:9092"
    kafka_consumer_group: str = "jira-citizen-group"
    
    # Kafka Topics (Events to listen to)
    topic_epic_create: str = "project.epic.create"
    topic_story_create: str = "project.story.create"
    topic_story_assign: str = "project.story.assign"
    topic_sprint_start: str = "project.sprint.start"
    
    # Gateway & Discovery
    gateway_url: str = "http://gateway-council:8000"
    
    # Metrics
    metrics_port: int = 9002
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
