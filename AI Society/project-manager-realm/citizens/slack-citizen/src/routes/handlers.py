"""Webhook event handlers using Command Pattern."""

from abc import ABC, abstractmethod
from typing import Any

from src.events import get_event_producer
from src.utils.mapping import (
    map_slack_command_to_internal_event,
    map_slack_interaction_to_internal_event,
    map_slack_message_to_internal_event,
)
from src.utils.observability import get_logger

logger = get_logger(__name__)


class WebhookEventHandler(ABC):
    """Abstract base for webhook event handlers (Command Pattern)."""

    @abstractmethod
    async def handle(self, event: dict[str, Any], tenant_id: str) -> None:
        """Handle a webhook event."""
        pass


class SlackMessageHandler(WebhookEventHandler):
    """Handles Slack message events."""

    async def handle(self, event_wrapper: Any, message: Any, tenant_id: str) -> None:
        """Handle a message event from Slack."""
        try:
            # Map to internal event
            internal_event = map_slack_message_to_internal_event(
                event_wrapper, message, tenant_id
            )

            # Publish to internal event bus
            producer = await get_event_producer()
            await producer.publish_event(
                topic="slack.message.received",
                event=internal_event.model_dump(),
                key=internal_event.event_id,
            )

            logger.info(
                "slack_message_published_to_bus",
                event_id=internal_event.event_id,
                tenant_id=tenant_id,
            )

        except Exception as e:
            logger.error(
                "failed_to_handle_slack_message",
                event_id=event_wrapper.event_id,
                tenant_id=tenant_id,
                error=str(e),
            )
            raise


class SlackAppMentionHandler(WebhookEventHandler):
    """Handles Slack app mention events."""

    async def handle(self, event_wrapper: Any, app_mention: Any, tenant_id: str) -> None:
        """Handle an app mention event."""
        try:
            logger.info(
                "slack_app_mention_received",
                tenant_id=tenant_id,
                user=app_mention.get("user"),
                channel=app_mention.get("channel"),
            )

            # Map app mention to message for now (can be specialized later)
            internal_event = map_slack_message_to_internal_event(
                event_wrapper,
                type("SlackMessage", (), {
                    "user": app_mention.get("user"),
                    "channel": app_mention.get("channel"),
                    "text": app_mention.get("text"),
                    "ts": app_mention.get("ts"),
                    "thread_ts": app_mention.get("thread_ts"),
                    "channel_type": "channel",
                    "subtype": "app_mention",
                })(),
                tenant_id,
            )

            # Publish to internal event bus
            producer = await get_event_producer()
            await producer.publish_event(
                topic="slack.app.mention.received",
                event=internal_event.model_dump(),
                key=internal_event.event_id,
            )

        except Exception as e:
            logger.error(
                "failed_to_handle_app_mention",
                tenant_id=tenant_id,
                error=str(e),
            )
            raise


class SlackCommandHandler(WebhookEventHandler):
    """Handles Slack slash command events."""

    async def handle(self, slack_command: Any, tenant_id: str) -> None:
        """Handle a slash command from Slack."""
        try:
            # Map to internal event
            internal_event = map_slack_command_to_internal_event(
                slack_command, tenant_id
            )

            # Publish to internal event bus
            producer = await get_event_producer()
            await producer.publish_event(
                topic="slack.command.invoked",
                event=internal_event.model_dump(),
                key=internal_event.event_id,
            )

            logger.info(
                "slack_command_published_to_bus",
                event_id=internal_event.event_id,
                command=slack_command.command,
                tenant_id=tenant_id,
            )

        except Exception as e:
            logger.error(
                "failed_to_handle_slash_command",
                command=slack_command.command,
                tenant_id=tenant_id,
                error=str(e),
            )
            raise


class SlackInteractionHandler(WebhookEventHandler):
    """Handles Slack interactive component events."""

    async def handle(self, slack_interaction: Any, tenant_id: str) -> None:
        """Handle an interaction event (button click, modal submission, etc.)."""
        try:
            # Map to internal event
            internal_event = map_slack_interaction_to_internal_event(
                slack_interaction, tenant_id
            )

            # Publish to internal event bus
            producer = await get_event_producer()
            await producer.publish_event(
                topic="slack.interaction.triggered",
                event=internal_event.model_dump(),
                key=internal_event.event_id,
            )

            logger.info(
                "slack_interaction_published_to_bus",
                event_id=internal_event.event_id,
                interaction_type=slack_interaction.type,
                tenant_id=tenant_id,
            )

        except Exception as e:
            logger.error(
                "failed_to_handle_interaction",
                interaction_type=slack_interaction.type,
                tenant_id=tenant_id,
                error=str(e),
            )
            raise
