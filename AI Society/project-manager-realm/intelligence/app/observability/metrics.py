# app/observability/metrics.py
"""Prometheus metrics setup"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import time
from typing import Callable
from functools import wraps
import structlog

logger = structlog.get_logger()

# Create registry
registry = CollectorRegistry()

# Define metrics
request_count = Counter(
    "intelligence_requests_total",
    "Total requests to Intelligence Service",
    ["method", "endpoint", "status"],
    registry=registry,
)

request_duration = Histogram(
    "intelligence_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
    registry=registry,
)

llm_tokens_total = Counter(
    "intelligence_llm_tokens_total",
    "Total LLM tokens used",
    ["provider", "model", "token_type"],
    registry=registry,
)

llm_cost_total = Counter(
    "intelligence_llm_cost_total",
    "Total LLM API cost in USD",
    ["provider", "model"],
    registry=registry,
)

vector_db_operations = Counter(
    "intelligence_vector_db_operations_total",
    "Vector database operations",
    ["operation", "provider"],
    registry=registry,
)

kafka_messages_processed = Counter(
    "intelligence_kafka_messages_processed_total",
    "Total Kafka messages processed",
    ["topic", "status"],
    registry=registry,
)

active_conversations = Gauge(
    "intelligence_active_conversations",
    "Number of active conversations",
    registry=registry,
)

db_connection_pool_size = Gauge(
    "intelligence_db_connection_pool_size",
    "Database connection pool size",
    registry=registry,
)


def setup_metrics() -> None:
    """Initialize metrics collection"""
    logger.info("metrics_initialized", registry=str(registry))


def track_request(endpoint: str):
    """Decorator to track HTTP requests"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                status = 200
                return result
            except Exception as e:
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                request_duration.labels(method="HTTP", endpoint=endpoint).observe(duration)
                logger.info(
                    "request_completed",
                    endpoint=endpoint,
                    duration_seconds=duration,
                    status=status,
                )
        
        return wrapper
    return decorator


def track_llm_call(provider: str, model: str):
    """Decorator to track LLM API calls and costs"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                logger.info(
                    "llm_call_completed",
                    provider=provider,
                    model=model,
                    duration_seconds=duration,
                )
        
        return wrapper
    return decorator


def get_metrics() -> bytes:
    """Get Prometheus metrics in text format"""
    return generate_latest(registry)
