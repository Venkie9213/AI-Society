"""Slack webhook handlers for inbound events."""

import json
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import ValidationError

from src.clients import get_slack_client
from src.events import get_event_producer
from src.schemas import SlackCommand, SlackEventWrapper, SlackInteraction, SlackMessage
from src.utils.mapping import (
    map_slack_command_to_internal_event,
    map_slack_interaction_to_internal_event,
    map_slack_message_to_internal_event,
)
from src.utils.observability import (
    get_logger,
    get_tenant_id,
    slack_messages_processing_duration,
    slack_messages_received,
)

router = APIRouter(prefix="/webhooks/slack", tags=["webhooks"])
logger = get_logger(__name__)


@router.post("/events")
async def slack_events(request: Request) -> dict[str, Any]:
    """
    Handle Slack Events API callbacks.
    
    Processes incoming Slack events (messages, reactions, etc.) and publishes
    them to the internal event bus.
    """
    tenant_id = get_tenant_id(request)
    
    # Parse body (already read by signature verification middleware)
    body = getattr(request.state, "body", None)
    if not body:
        body = await request.body()
    
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    # Handle URL verification challenge
    if data.get("type") == "url_verification":
        logger.info("slack_url_verification", tenant_id=tenant_id)
        return {"challenge": data.get("challenge")}

    # Parse event wrapper
    try:
        event_wrapper = SlackEventWrapper(**data)
    except ValidationError as e:
        logger.error(
            "slack_event_validation_failed",
            tenant_id=tenant_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid event format",
        )

    # Track metrics
    event_type = event_wrapper.event.get("type", "unknown")
    slack_messages_received.labels(
        tenant_id=tenant_id,
        channel_type=event_type,
    ).inc()

    # Process event with timing
    with slack_messages_processing_duration.labels(tenant_id=tenant_id).time():
        await _process_slack_event(event_wrapper, tenant_id)

    # Return 200 OK immediately (async processing)
    return {"ok": True}


async def _process_slack_event(
    event_wrapper: SlackEventWrapper,
    tenant_id: str,
) -> None:
    """
    Process a Slack event and publish to internal event bus.
    
    Args:
        event_wrapper: Slack event wrapper
        tenant_id: Tenant ID
    """
    event_type = event_wrapper.event.get("type")
    
    if event_type == "message":
        await _handle_message_event(event_wrapper, tenant_id)
    elif event_type == "app_mention":
        await _handle_app_mention_event(event_wrapper, tenant_id)
    else:
        logger.debug(
            "unhandled_slack_event_type",
            event_type=event_type,
            tenant_id=tenant_id,
        )


async def _handle_message_event(
    event_wrapper: SlackEventWrapper,
    tenant_id: str,
) -> None:
    """Handle message events."""
    try:
        raw = event_wrapper.event

        # Slack sometimes nests the actual message under the `message` key
        payload = raw.get("message", raw)

        # Normalize fields: prefer payload values, fall back to wrapper-level keys
        normalized = {
            "type": payload.get("type", "message"),
            "subtype": payload.get("subtype") or raw.get("subtype"),
            "user": payload.get("user") or raw.get("user"),
            "text": payload.get("text"),
            "ts": payload.get("ts") or payload.get("event_ts") or raw.get("ts"),
            "channel": raw.get("channel") or payload.get("channel") or raw.get("channel_id"),
            "thread_ts": payload.get("thread_ts") or raw.get("thread_ts"),
            "channel_type": raw.get("channel_type") or payload.get("channel_type"),
        }

        # Skip bot messages (bot_id present) and well-known subtypes
        if payload.get("bot_id") is not None or normalized["subtype"] in [
            "bot_message",
            "message_deleted",
        ]:
            return

        # If required fields are missing, skip gracefully (common for some IM events)
        missing = [k for k in ("user", "text") if not normalized.get(k)]
        if missing:
            logger.debug(
                "slack_message_missing_required_fields",
                tenant_id=tenant_id,
                missing_fields=missing,
                raw_event=raw,
            )
            return

        # Validate with Pydantic (ensures required fields present)
        message = SlackMessage(**normalized)

        # Skip edited messages explicitly (message_changed can be a top-level subtype)
        if normalized.get("subtype") == "message_changed":
            return

        # Map to internal event
        internal_event = map_slack_message_to_internal_event(
            event_wrapper,
            message,
            tenant_id,
        )

        # Publish to Kafka
        producer = await get_event_producer()
        await producer.publish_event(
            topic="message.received",
            event=internal_event.model_dump(mode="json"),
            key=internal_event.event_id,
        )

        # Add reaction to acknowledge receipt
        slack_client = get_slack_client()
        await slack_client.add_reaction(
            channel=message.channel,
            timestamp=message.ts,
            emoji="eyes",
            tenant_id=tenant_id,
        )

        logger.info(
            "slack_message_processed",
            event_id=internal_event.event_id,
            tenant_id=tenant_id,
            channel=message.channel,
        )

    except ValidationError as e:
        logger.error(
            "slack_message_validation_failed",
            tenant_id=tenant_id,
            error=str(e),
        )
    except Exception as e:
        logger.error(
            "slack_message_processing_failed",
            tenant_id=tenant_id,
            error=str(e),
            error_type=type(e).__name__,
        )


async def _handle_app_mention_event(
    event_wrapper: SlackEventWrapper,
    tenant_id: str,
) -> None:
    """Handle app mention events (when bot is @mentioned)."""
    # Similar to message event but specifically for mentions
    await _handle_message_event(event_wrapper, tenant_id)


@router.post("/commands")
async def slack_commands(request: Request) -> dict[str, Any]:
    """
    Handle Slack slash commands.
    
    Processes incoming slash commands and publishes them to the event bus.
    """
    tenant_id = get_tenant_id(request)
    
    # Parse form data
    form_data = await request.form()
    command_data = dict(form_data)

    try:
        command = SlackCommand(**command_data)
    except ValidationError as e:
        logger.error(
            "slack_command_validation_failed",
            tenant_id=tenant_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid command format",
        )

    # Map to internal event
    internal_event = map_slack_command_to_internal_event(command, tenant_id)

    # Publish to Kafka
    producer = await get_event_producer()
    await producer.publish_event(
        topic="slack.command.invoked",
        event=internal_event.model_dump(mode="json"),
        key=internal_event.event_id,
    )

    logger.info(
        "slack_command_processed",
        command=command.command,
        tenant_id=tenant_id,
        event_id=internal_event.event_id,
    )

    # Return immediate acknowledgment
    return {
        "response_type": "ephemeral",
        "text": f"Processing command: {command.command} {command.text}",
    }


@router.post("/interactions")
async def slack_interactions(request: Request) -> dict[str, Any]:
    """
    Handle Slack interactive components (buttons, modals, etc.).
    
    Processes interactive component callbacks and publishes them to the event bus.
    """
    tenant_id = get_tenant_id(request)
    
    # Parse form data (Slack sends interactions as form-encoded)
    form_data = await request.form()
    payload_json = form_data.get("payload")
    
    if not payload_json:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing payload",
        )

    try:
        payload = json.loads(payload_json)
        interaction = SlackInteraction(**payload)
    except (json.JSONDecodeError, ValidationError) as e:
        logger.error(
            "slack_interaction_validation_failed",
            tenant_id=tenant_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid interaction format",
        )

    # Map to internal event
    internal_event = map_slack_interaction_to_internal_event(interaction, tenant_id)

    # Publish to Kafka
    producer = await get_event_producer()
    await producer.publish_event(
        topic="slack.interaction.triggered",
        event=internal_event.model_dump(mode="json"),
        key=internal_event.event_id,
    )

    logger.info(
        "slack_interaction_processed",
        interaction_type=interaction.type,
        tenant_id=tenant_id,
        event_id=internal_event.event_id,
    )

    # Return acknowledgment
    return {"response_type": "ephemeral", "text": "Processing your action..."}
