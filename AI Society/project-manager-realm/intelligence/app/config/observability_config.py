# intelligence/service/app/config/observability_config.py
"""Observability configuration (logging, metrics, tracing)."""

import os
from pydantic_settings import BaseSettings


class ObservabilityConfig(BaseSettings):
    """Observability configuration."""
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    structured_logs: bool = True
    log_format: str = "json"  # "json" or "text"
    
    # Metrics
    enable_metrics: bool = True
    metrics_port: int = int(os.getenv("METRICS_PORT", 8001))
    metrics_path: str = "/metrics"
    
    # Tracing
    enable_tracing: bool = False  # Future: OpenTelemetry
    trace_sample_rate: float = 0.1
    
    # Correlation IDs
    enable_correlation_ids: bool = True
    correlation_id_header: str = "X-Correlation-ID"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
