# app/config.py
import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class LLMConfig(BaseSettings):
    """LLM Provider Configuration"""
    
    # Gemini Configuration (new unified SDK)
    gemini_api_key: str = Field(default="", description="Google Gemini API Key")
    gemini_model: str = Field(default="gemini-3-flash-preview", description="Gemini model version (default 3 Flash Preview - 2026)")
    
    # Claude Configuration (for future use)
    claude_api_key: str = Field(default="", description="Anthropic Claude API Key")
    claude_model: str = Field(default="claude-3.5-sonnet", description="Claude model version")
    
    # OpenAI Configuration (for future use)
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    openai_model: str = Field(default="gpt-4-turbo-preview", description="GPT model version")
    
    # LLM Behavior
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1000, gt=0)
    timeout_seconds: int = Field(default=30, gt=0)
    retry_attempts: int = Field(default=3, ge=1)
    retry_delay: float = Field(default=1.0, gt=0)
    
    # Provider Strategy
    primary_provider: str = Field(default="gemini", description="Primary LLM provider (gemini, claude, gpt4)")
    fallback_providers: List[str] = Field(default=["gemini"], description="Fallback providers in order")
    
    # Development Mode
    development_mode: bool = Field(default=True)
    mock_llm_responses: bool = Field(default=False)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class DatabaseConfig(BaseSettings):
    """Database Configuration"""
    
    database_url: str = Field(
        default="postgresql://intelligence:dev_password@localhost:5432/intelligence",
        description="PostgreSQL connection URL"
    )
    db_pool_size: int = Field(default=5, gt=0)
    db_max_overflow: int = Field(default=10, ge=0)
    db_echo: bool = Field(default=False, description="Enable SQL query logging")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class KafkaConfig(BaseSettings):
    """Kafka Configuration"""
    
    kafka_brokers: str = "localhost:9092"
    kafka_consumer_group: str = "intelligence-service"
    kafka_security_protocol: str = "PLAINTEXT"
    
    # Topics
    topic_slack_message_received: str = "slack.message.received"
    topic_slack_reply_requested: str = "slack.reply.requested"
    topic_conversations: str = "intelligence.conversations"
    topic_dlq: str = "intelligence-dlq"
    
    # Consumer settings
    kafka_auto_offset_reset: str = "earliest"
    kafka_session_timeout_ms: int = 30000
    kafka_heartbeat_interval_ms: int = 10000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class VectorStoreConfig(BaseSettings):
    """Vector Store Configuration"""
    
    vector_provider: str = "chroma"  # chroma or pinecone
    vector_dimension: int = 1536
    vector_similarity_threshold: float = 0.7
    
    # Chroma Configuration (development)
    chroma_persist_dir: str = "./chroma_data"
    
    # Pinecone Configuration (production)
    pinecone_api_key: str = ""
    pinecone_environment: str = "us-west1-gcp"
    
    # Embedding Provider
    embedding_provider: str = "gemini"  # gemini, openai, cohere
    embedding_cache_size: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class CostTrackingConfig(BaseSettings):
    """Cost Tracking Configuration"""
    
    track_costs: bool = True
    cost_budget_monthly_cents: int = 100000  # $1000/month
    cost_alert_threshold: int = 80  # Alert at 80% of budget
    cost_currency: str = "USD"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class LoggingConfig(BaseSettings):
    """Logging Configuration"""
    
    log_level: str = "info"
    structured_logs: bool = True
    log_format: str = "json"  # json or text
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class AppConfig(BaseSettings):
    """Main Application Configuration"""
    
    app_name: str = Field(default="Intelligence Service")
    app_version: str = Field(default="0.1.0")
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    debug: bool = Field(default=False)
    
    # Multi-tenancy
    tenant_isolation_enabled: bool = Field(default=True)
    jwt_secret: str = Field(default="", description="JWT signing secret (required in production)")
    
    # CORS
    cors_origins: List[str] = Field(default=["*"], description="Allowed origins for CORS")
    cors_credentials: bool = Field(default=True)
    cors_methods: List[str] = Field(default=["*"])
    cors_headers: List[str] = Field(default=["*"])
    
    # Sub-configs
    llm: LLMConfig = Field(default_factory=LLMConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    kafka: KafkaConfig = Field(default_factory=KafkaConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    cost_tracking: CostTrackingConfig = Field(default_factory=CostTrackingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Instantiate global config
config = AppConfig()


def get_provider_config() -> dict:
    """Get provider router configuration from app config
    
    Returns:
        Dictionary with provider router configuration
    """
    return {
        "primary_provider": config.llm.primary_provider,
        "fallback_providers": config.llm.fallback_providers,
        "provider_configs": {
            "gemini": {
                "api_key": config.llm.gemini_api_key,
                "model": config.llm.gemini_model,
                "temperature": config.llm.temperature,
                "max_tokens": config.llm.max_tokens,
                "timeout_seconds": config.llm.timeout_seconds,
            },
            "claude": {
                "api_key": config.llm.claude_api_key,
                "model": config.llm.claude_model,
                "temperature": config.llm.temperature,
                "max_tokens": config.llm.max_tokens,
                "timeout_seconds": config.llm.timeout_seconds,
            },
            "openai": {
                "api_key": config.llm.openai_api_key,
                "model": config.llm.openai_model,
                "temperature": config.llm.temperature,
                "max_tokens": config.llm.max_tokens,
                "timeout_seconds": config.llm.timeout_seconds,
            },
        },
    }
