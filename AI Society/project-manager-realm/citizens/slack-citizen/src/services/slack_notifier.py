"""Slack notification service using message builders for formatting."""

from typing import Any, Dict

from src.clients import get_slack_client
from src.clients.message_builders import (
    ClarificationNotificationBuilder,
    PulseNotificationBuilder,
    RequirementNotificationBuilder,
)
from src.schemas import (
    RequirementCreatedPayload,
    RequirementClarificationCompletedPayload,
    PulseExecutionFailedPayload,
    SlackReplyRequestedPayload,
)
from src.utils.observability import get_logger

logger = get_logger(__name__)


class SlackNotifier:
    """Sends Slack notifications using builder pattern for formatting.

    Keeps Slack-specific code isolated so other modules remain agnostic.
    """

    def __init__(self) -> None:
        """Initialize the notifier."""
        self._client = None

    def _client_instance(self):
        """Lazy-load Slack client."""
        if self._client is None:
            self._client = get_slack_client()
        return self._client

    async def notify_requirement_created(self, payload: Dict[str, Any], tenant_id: str) -> None:
        """Send notification when a requirement is created."""
        req = RequirementCreatedPayload(**payload)
        channel_id = req.metadata.get("slack_channel_id")
        thread_ts = req.metadata.get("slack_thread_ts")

        if not channel_id:
            logger.warning(
                "no_slack_channel_for_requirement",
                requirement_id=req.requirement_id,
                tenant_id=tenant_id,
            )
            return

        blocks = RequirementNotificationBuilder.build_creation_blocks(
            requirement_id=req.requirement_id,
            title=req.title,
            description=req.description,
        )
        text = RequirementNotificationBuilder.get_creation_text(req.title)

        await self._client_instance().post_message(
            channel=channel_id,
            text=text,
            blocks=blocks,
            thread_ts=thread_ts,
            tenant_id=tenant_id,
        )

        logger.info(
            "requirement_notification_sent",
            requirement_id=req.requirement_id,
            tenant_id=tenant_id,
            channel=channel_id,
        )

    async def notify_clarification_completed(self, payload: Dict[str, Any], tenant_id: str) -> None:
        """Send notification when clarification is completed."""
        clar = RequirementClarificationCompletedPayload(**payload)
        channel_id = clar.metadata.get("slack_channel_id")
        thread_ts = clar.metadata.get("slack_thread_ts")

        if not channel_id:
            logger.warning(
                "no_slack_channel_for_clarification",
                requirement_id=clar.requirement_id,
                tenant_id=tenant_id,
            )
            return

        blocks = ClarificationNotificationBuilder.build_completion_blocks(
            requirement_id=clar.requirement_id,
            summary=clar.clarification_summary,
            prd_content=clar.prd_content,
        )
        text = ClarificationNotificationBuilder.get_completion_text(clar.requirement_id)

        await self._client_instance().post_message(
            channel=channel_id,
            text=text,
            blocks=blocks,
            thread_ts=thread_ts,
            tenant_id=tenant_id,
        )

        logger.info(
            "clarification_notification_sent",
            requirement_id=clar.requirement_id,
            tenant_id=tenant_id,
            channel=channel_id,
        )

    async def notify_pulse_failure(self, payload: Dict[str, Any], tenant_id: str) -> None:
        """Send notification when a pulse execution fails."""
        pf = PulseExecutionFailedPayload(**payload)
        channel_id = pf.metadata.get("slack_channel_id")

        if not channel_id:
            logger.warning(
                "no_slack_channel_for_pulse_failure",
                pulse_id=pf.pulse_id,
                tenant_id=tenant_id,
            )
            return

        blocks = PulseNotificationBuilder.build_failure_blocks(
            pulse_name=pf.pulse_name,
            execution_id=pf.execution_id,
            error_message=pf.error_message,
        )
        text = PulseNotificationBuilder.get_failure_text(pf.pulse_name)

        await self._client_instance().post_message(
            channel=channel_id,
            text=text,
            blocks=blocks,
            tenant_id=tenant_id,
        )

        logger.info(
            "pulse_failure_notification_sent",
            pulse_id=pf.pulse_id,
            tenant_id=tenant_id,
        )

    async def send_slack_reply(self, payload: Dict[str, Any], tenant_id: str) -> None:
        """Send a reply to Slack from Intelligence Service."""
        reply = SlackReplyRequestedPayload(**payload)
        logger.info(
            "sending_slack_reply",
            channel=reply.slack_channel_id,
            thread_ts=reply.slack_thread_ts,
            tenant_id=tenant_id,
        )

        await self._client_instance().post_message(
            channel=reply.slack_channel_id,
            text=reply.message_text,
            blocks=reply.blocks,
            thread_ts=reply.slack_thread_ts,
            tenant_id=tenant_id,
        )

        logger.info(
            "slack_reply_sent",
            channel=reply.slack_channel_id,
            thread_ts=reply.slack_thread_ts,
            tenant_id=tenant_id,
        )
