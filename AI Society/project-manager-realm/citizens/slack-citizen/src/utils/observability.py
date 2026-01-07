"""Utility module for structured logging and metrics."""

import logging
import sys
from contextvars import ContextVar
from typing import Any, Optional

import structlog
from prometheus_client import Counter, Histogram, start_http_server

from src.config import settings

# Context variables for correlation and tenant IDs
correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)
tenant_id_var: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)


def configure_logging() -> None:
    """Configure structured logging with structlog."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if not settings.is_development
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger with the given name."""
    return structlog.get_logger(name)


def add_context(**kwargs: Any) -> None:
    """Add context to all subsequent log messages."""
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context(*keys: str) -> None:
    """Clear specific context keys."""
    structlog.contextvars.unbind_contextvars(*keys)


# Prometheus Metrics
slack_messages_received = Counter(
    "slack_messages_received_total",
    "Total number of Slack messages received",
    ["tenant_id", "channel_type"],
)

slack_messages_processing_duration = Histogram(
    "slack_messages_processing_seconds",
    "Time spent processing Slack messages",
    ["tenant_id"],
)

slack_api_calls = Counter(
    "slack_api_calls_total",
    "Total number of Slack API calls",
    ["tenant_id", "endpoint", "status"],
)

slack_api_errors = Counter(
    "slack_api_errors_total",
    "Total number of Slack API errors",
    ["tenant_id", "error_type"],
)

kafka_messages_published = Counter(
    "kafka_messages_published_total",
    "Total number of messages published to Kafka",
    ["tenant_id", "topic"],
)

kafka_messages_consumed = Counter(
    "kafka_messages_consumed_total",
    "Total number of messages consumed from Kafka",
    ["tenant_id", "topic"],
)

kafka_publish_errors = Counter(
    "kafka_publish_errors_total",
    "Total number of Kafka publish errors",
    ["tenant_id", "topic", "error_type"],
)

event_processing_duration = Histogram(
    "event_processing_seconds",
    "Time spent processing events",
    ["tenant_id", "event_type"],
)


def start_metrics_server() -> None:
    """Start Prometheus metrics HTTP server."""
    if settings.enable_metrics:
        start_http_server(settings.prometheus_port)
        logger = get_logger(__name__)
        logger.info(
            "metrics_server_started",
            port=settings.prometheus_port,
        )
