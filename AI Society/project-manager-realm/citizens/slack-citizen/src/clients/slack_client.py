"""Slack Web API client with retry and metrics tracking."""

from typing import Any, Optional

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from src.clients.slack_client_repository import SlackClientRepository
from src.config import settings
from src.utils.observability import get_logger, slack_api_calls, slack_api_errors
from src.utils.retry import retry_with_dlq

logger = get_logger(__name__)


class SlackClient:
    """Client for interacting with Slack Web API with metrics and retry.

    Uses Repository pattern for data access layer.
    """

    def __init__(self, bot_token: Optional[str] = None) -> None:
        """
        Initialize Slack client.

        Args:
            bot_token: Slack bot OAuth token (defaults to settings)
        """
        self.bot_token = bot_token or settings.project_manager_slack_bot_token
        sdk_client = AsyncWebClient(token=self.bot_token)
        self._repository = SlackClientRepository(sdk_client)

    @retry_with_dlq(
        max_attempts=3,
        dlq_topic="slack.notifications.failed",
    )
    async def post_message(
        self,
        channel: str,
        text: Optional[str] = None,
        blocks: Optional[list[dict[str, Any]]] = None,
        thread_ts: Optional[str] = None,
        tenant_id: str = "unknown",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Post a message to Slack."""
        try:
            response = await self._repository.post_message(
                channel=channel,
                text=text,
                blocks=blocks,
                thread_ts=thread_ts,
                **kwargs,
            )

            # Track metrics
            slack_api_calls.labels(
                tenant_id=tenant_id,
                endpoint="chat.postMessage",
                status="success",
            ).inc()

            logger.info(
                "slack_message_posted",
                channel=channel,
                thread_ts=thread_ts,
                tenant_id=tenant_id,
                message_ts=response.get("ts"),
            )

            return response

        except SlackApiError as e:
            # Track error metrics
            slack_api_errors.labels(
                tenant_id=tenant_id,
                error_type=e.response["error"],
            ).inc()

            slack_api_calls.labels(
                tenant_id=tenant_id,
                endpoint="chat.postMessage",
                status="error",
            ).inc()

            logger.error(
                "slack_message_post_failed",
                channel=channel,
                tenant_id=tenant_id,
                error=e.response["error"],
                error_detail=str(e),
            )
            raise

    @retry_with_dlq(
        max_attempts=3,
        dlq_topic="slack.notifications.failed",
    )
    async def update_message(
        self,
        channel: str,
        ts: str,
        text: Optional[str] = None,
        blocks: Optional[list[dict[str, Any]]] = None,
        tenant_id: str = "unknown",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Update a Slack message."""
        try:
            response = await self._repository.update_message(
                channel=channel,
                ts=ts,
                text=text,
                blocks=blocks,
                **kwargs,
            )

            slack_api_calls.labels(
                tenant_id=tenant_id,
                endpoint="chat.update",
                status="success",
            ).inc()

            logger.info(
                "slack_message_updated",
                channel=channel,
                ts=ts,
                tenant_id=tenant_id,
            )

            return response

        except SlackApiError as e:
            slack_api_errors.labels(
                tenant_id=tenant_id,
                error_type=e.response["error"],
            ).inc()

            slack_api_calls.labels(
                tenant_id=tenant_id,
                endpoint="chat.update",
                status="error",
            ).inc()

            logger.error(
                "slack_message_update_failed",
                channel=channel,
                ts=ts,
                tenant_id=tenant_id,
                error=e.response["error"],
            )
            raise

    async def add_reaction(
        self,
        channel: str,
        timestamp: str,
        emoji: str,
        tenant_id: str = "unknown",
    ) -> dict[str, Any]:
        """Add a reaction to a message."""
        try:
            response = await self._repository.add_reaction(
                channel=channel,
                timestamp=timestamp,
                emoji=emoji,
            )

            slack_api_calls.labels(
                tenant_id=tenant_id,
                endpoint="reactions.add",
                status="success",
            ).inc()

            logger.debug(
                "slack_reaction_added",
                channel=channel,
                timestamp=timestamp,
                emoji=emoji,
                tenant_id=tenant_id,
            )

            return response

        except SlackApiError as e:
            slack_api_errors.labels(
                tenant_id=tenant_id,
                error_type=e.response["error"],
            ).inc()

            logger.warning(
                "slack_reaction_add_failed",
                channel=channel,
                timestamp=timestamp,
                emoji=emoji,
                tenant_id=tenant_id,
                error=e.response["error"],
            )
            # Don't raise - reactions are non-critical
            return {}


# Global client instance
_slack_client_instance: Optional[SlackClient] = None


def get_slack_client() -> SlackClient:
    """Get or create the global Slack client instance."""
    global _slack_client_instance
    
    if _slack_client_instance is None:
        _slack_client_instance = SlackClient()
    
    return _slack_client_instance
