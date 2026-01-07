"""Event mapping utilities for transforming Slack events to internal events.

Uses factory pattern to keep mapping logic separate and testable.
"""

from typing import Any

from src.utils.event_factories import (
    SlackCommandEventFactory,
    SlackInteractionEventFactory,
    SlackMessageEventFactory,
)
from src.utils.observability import get_logger

logger = get_logger(__name__)

# Re-export factories for backward compatibility
__all__ = [
    "SlackMessageEventFactory",
    "SlackCommandEventFactory",
    "SlackInteractionEventFactory",
    "map_slack_message_to_internal_event",
    "map_slack_command_to_internal_event",
    "map_slack_interaction_to_internal_event",
    "extract_slack_metadata_from_event",
]

# Wrapper functions for backward compatibility
def map_slack_message_to_internal_event(slack_event, message, tenant_id):
    """Backward compatible wrapper for SlackMessageEventFactory."""
    return SlackMessageEventFactory.create(slack_event, message, tenant_id)


def map_slack_command_to_internal_event(slack_command, tenant_id):
    """Backward compatible wrapper for SlackCommandEventFactory."""
    return SlackCommandEventFactory.create(slack_command, tenant_id)


def map_slack_interaction_to_internal_event(slack_interaction, tenant_id):
    """Backward compatible wrapper for SlackInteractionEventFactory."""
    return SlackInteractionEventFactory.create(slack_interaction, tenant_id)


def extract_slack_metadata_from_event(event) -> dict[str, Any]:
    """
    Extract Slack-specific metadata from an internal event.

    Used to determine where to send outbound notifications.

    Args:
        event: Internal event envelope

    Returns:
        Dictionary containing Slack channel/thread information
    """
    metadata = event.payload.get("metadata", {})

    return {
        "channel_id": metadata.get("slack_channel_id"),
        "thread_ts": metadata.get("slack_thread_ts") or metadata.get("thread_ts"),
        "message_ts": metadata.get("slack_message_ts"),
        "team_id": metadata.get("slack_team_id"),
    }
