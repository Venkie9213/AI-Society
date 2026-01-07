"""Event mapping utilities for transforming Slack events to internal events."""

import uuid
from datetime import datetime, timezone
from typing import Any

from src.schemas.internal_schemas import (
    EventEnvelope,
    SlackCommandInvokedPayload,
    SlackInteractionTriggeredPayload,
    SlackMessageReceivedPayload,
)
from src.schemas.slack_schemas import (
    SlackCommand,
    SlackEventWrapper,
    SlackInteraction,
    SlackMessage,
)
from src.utils.observability import get_logger

logger = get_logger(__name__)


def generate_event_id() -> str:
    """Generate a unique event ID."""
    return str(uuid.uuid4())


def generate_entity_id(prefix: str) -> str:
    """Generate a unique entity ID with a prefix."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def map_slack_message_to_internal_event(
    slack_event: SlackEventWrapper,
    message: SlackMessage,
    tenant_id: str,
) -> EventEnvelope:
    """
    Map Slack message event to internal slack.message.received event.
    
    Args:
        slack_event: Slack event wrapper
        message: Slack message payload
        tenant_id: Internal tenant ID
    
    Returns:
        Internal event envelope
    """
    message_id = generate_entity_id("msg")
    
    payload = SlackMessageReceivedPayload(
        message_id=message_id,
        slack_user_id=message.user,
        slack_channel_id=message.channel,
        slack_team_id=slack_event.team_id,
        text=message.text,
        thread_ts=message.thread_ts,
        message_ts=message.ts,
        channel_type=message.channel_type or "channel",
        metadata={
            "slack_event_id": slack_event.event_id,
            "slack_event_time": slack_event.event_time,
            "message_subtype": message.subtype,
        },
    )

    event = EventEnvelope(
        event_id=generate_event_id(),
        occurred_at=datetime.fromtimestamp(slack_event.event_time, tz=timezone.utc),
        tenant_id=tenant_id,
        source="slack-citizen",
        payload_version="v1",
        payload=payload.model_dump(),
    )

    logger.debug(
        "slack_message_mapped",
        tenant_id=tenant_id,
        event_id=event.event_id,
        message_id=message_id,
        slack_event_id=slack_event.event_id,
    )

    return event


def map_slack_command_to_internal_event(
    slack_command: SlackCommand,
    tenant_id: str,
) -> EventEnvelope:
    """
    Map Slack slash command to internal slack.command.invoked event.
    
    Args:
        slack_command: Slack command payload
        tenant_id: Internal tenant ID
    
    Returns:
        Internal event envelope
    """
    command_id = generate_entity_id("cmd")
    
    payload = SlackCommandInvokedPayload(
        command_id=command_id,
        slack_user_id=slack_command.user_id,
        slack_team_id=slack_command.team_id,
        slack_channel_id=slack_command.channel_id,
        command=slack_command.command,
        arguments=slack_command.text,
        response_url=slack_command.response_url,
        trigger_id=slack_command.trigger_id,
    )

    event = EventEnvelope(
        event_id=generate_event_id(),
        occurred_at=datetime.now(timezone.utc),
        tenant_id=tenant_id,
        source="slack-citizen",
        payload_version="v1",
        payload=payload.model_dump(),
    )

    logger.debug(
        "slack_command_mapped",
        tenant_id=tenant_id,
        event_id=event.event_id,
        command_id=command_id,
        command=slack_command.command,
    )

    return event


def map_slack_interaction_to_internal_event(
    slack_interaction: SlackInteraction,
    tenant_id: str,
) -> EventEnvelope:
    """
    Map Slack interaction to internal slack.interaction.triggered event.
    
    Args:
        slack_interaction: Slack interaction payload
        tenant_id: Internal tenant ID
    
    Returns:
        Internal event envelope
    """
    interaction_id = generate_entity_id("int")
    
    payload = SlackInteractionTriggeredPayload(
        interaction_id=interaction_id,
        interaction_type=slack_interaction.type,
        slack_user_id=slack_interaction.user["id"],
        slack_team_id=slack_interaction.team["id"],
        slack_channel_id=slack_interaction.channel["id"] if slack_interaction.channel else None,
        actions=slack_interaction.actions or [],
        response_url=slack_interaction.response_url,
        trigger_id=slack_interaction.trigger_id,
    )

    event = EventEnvelope(
        event_id=generate_event_id(),
        occurred_at=datetime.now(timezone.utc),
        tenant_id=tenant_id,
        source="slack-citizen",
        payload_version="v1",
        payload=payload.model_dump(),
    )

    logger.debug(
        "slack_interaction_mapped",
        tenant_id=tenant_id,
        event_id=event.event_id,
        interaction_id=interaction_id,
        interaction_type=slack_interaction.type,
    )

    return event


def extract_slack_metadata_from_event(event: EventEnvelope) -> dict[str, Any]:
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
