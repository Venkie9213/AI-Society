# intelligence/service/app/config/app_config.py
"""Application configuration (FastAPI, ports, environment)."""

import os
from typing import List, Optional
from pathlib import Path
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """Application-level configuration - all settings consolidated."""
    
    # Application
    app_name: str = os.getenv("APP_NAME", "AI Society Intelligence Service")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    environment: str = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development"))
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
    
    # LLM Configuration  
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://intelligence:dev_password@postgres:5432/intelligence")
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "5"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    
    # Kafka
    kafka_brokers: str = os.getenv("KAFKA_BROKERS", "localhost:9092")
    kafka_consumer_group: str = os.getenv("KAFKA_CONSUMER_GROUP", "intelligence-service")
    
    # Vector Store
    vector_store_provider: str = os.getenv("VECTOR_STORE_PROVIDER", "chroma")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "info")
    structured_logs: bool = True
    log_format: str = "json"
    
    # Metrics
    enable_metrics: bool = True
    metrics_port: int = int(os.getenv("METRICS_PORT", "8001"))
    metrics_path: str = "/metrics"
    
    # Tracing
    enable_tracing: bool = False
    trace_sample_rate: float = 0.1
    
    # Correlation IDs
    enable_correlation_ids: bool = True
    correlation_id_header: str = "X-Correlation-ID"
    
    # Intelligence Paths
    cache_configs: bool = True
    config_cache_ttl_seconds: int = 3600
    default_provider: str = os.getenv("DEFAULT_PROVIDER", "gemini")
    default_model: str = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash-lite")
    default_temperature: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
    default_max_tokens: int = int(os.getenv("DEFAULT_MAX_TOKENS", "1000"))
    
    # Intelligence directory paths (mounted in /app/app in container)
    models_path: Path = Path("/app/app/models")
    agents_path: Path = Path("/app/app/agents")
    prompts_path: Path = Path("/app/app/prompts")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env
