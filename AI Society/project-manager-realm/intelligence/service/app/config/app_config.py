# intelligence/service/app/config/app_config.py
"""Application configuration (FastAPI, ports, environment)."""

import os
from typing import List
from pydantic import BaseSettings


class AppConfig(BaseSettings):
    """Application-level configuration."""
    
    app_name: str = os.getenv("APP_NAME", "AI Society Intelligence Service")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", 8000))
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8001",
    ]
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
