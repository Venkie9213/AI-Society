"""Utility module initialization."""

from src.utils.id_generator import (
    generate_entity_id,
    generate_event_id,
)
from src.utils.mapping import (
    extract_slack_metadata_from_event,
    map_slack_command_to_internal_event,
    map_slack_interaction_to_internal_event,
    map_slack_message_to_internal_event,
)
from src.utils.observability import (
    add_context,
    clear_context,
    configure_logging,
    get_logger,
    start_metrics_server,
)
from src.utils.retry import (
    RetryExhaustedError,
    publish_to_dlq,
    retry_async,
    retry_with_dlq,
)

__all__ = [
    # Observability
    "configure_logging",
    "get_logger",
    "add_context",
    "clear_context",
    "start_metrics_server",
    # Retry
    "retry_with_dlq",
    "retry_async",
    "publish_to_dlq",
    "RetryExhaustedError",
    # Mapping
    "generate_event_id",
    "generate_entity_id",
    "map_slack_message_to_internal_event",
    "map_slack_command_to_internal_event",
    "map_slack_interaction_to_internal_event",
    "extract_slack_metadata_from_event",
]
