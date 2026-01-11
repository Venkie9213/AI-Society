"""Observability module for logging, metrics, and tracing."""

from src.utils.observability.logging import configure_logging, get_logger, add_context, clear_context
from src.utils.observability.metrics import (
    slack_messages_received,
    slack_messages_processing_duration,
    slack_api_calls,
    slack_api_errors,
    kafka_messages_published,
    kafka_publish_errors,
    kafka_messages_consumed,
    event_processing_duration,
)
from src.utils.observability.context import get_tenant_id, get_correlation_id
from src.utils.observability.server import start_metrics_server

__all__ = [
    "configure_logging",
    "get_logger",
    "add_context",
    "clear_context",
    "slack_messages_received",
    "slack_messages_processing_duration",
    "slack_api_calls",
    "slack_api_errors",
    "kafka_messages_published",
    "kafka_publish_errors",
    "kafka_messages_consumed",
    "event_processing_duration",
    "start_metrics_server",
    "get_tenant_id",
    "get_correlation_id",
]
