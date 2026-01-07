"""Slack Web API client for outbound notifications."""

from typing import Any, Optional

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from src.config import settings
from src.utils.observability import get_logger, slack_api_calls, slack_api_errors
from src.utils.retry import retry_with_dlq

logger = get_logger(__name__)


class SlackClient:
    """Client for interacting with Slack Web API."""

    def __init__(self, bot_token: Optional[str] = None) -> None:
        """
        Initialize Slack client.
        
        Args:
            bot_token: Slack bot OAuth token (defaults to settings)
        """
        self.bot_token = bot_token or settings.slack_bot_token
        self.client = AsyncWebClient(token=self.bot_token)

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
        """
        Post a message to a Slack channel.
        
        Args:
            channel: Channel ID or name
            text: Message text (fallback for notifications)
            blocks: Slack Block Kit blocks for rich formatting
            thread_ts: Thread timestamp to reply in thread
            tenant_id: Tenant ID for metrics
            **kwargs: Additional arguments for chat.postMessage
        
        Returns:
            Slack API response
        
        Raises:
            SlackApiError: If the API call fails
        """
        try:
            response = await self.client.chat_postMessage(
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

            return response.data

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
        """
        Update an existing Slack message.
        
        Args:
            channel: Channel ID
            ts: Message timestamp to update
            text: New message text
            blocks: New Slack blocks
            tenant_id: Tenant ID for metrics
            **kwargs: Additional arguments for chat.update
        
        Returns:
            Slack API response
        """
        try:
            response = await self.client.chat_update(
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

            return response.data

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
        """
        Add a reaction emoji to a message.
        
        Args:
            channel: Channel ID
            timestamp: Message timestamp
            emoji: Emoji name (without colons)
            tenant_id: Tenant ID for metrics
        
        Returns:
            Slack API response
        """
        try:
            response = await self.client.reactions_add(
                channel=channel,
                timestamp=timestamp,
                name=emoji,
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

            return response.data

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

    async def open_modal(
        self,
        trigger_id: str,
        view: dict[str, Any],
        tenant_id: str = "unknown",
    ) -> dict[str, Any]:
        """
        Open a modal dialog.
        
        Args:
            trigger_id: Trigger ID from interaction
            view: Modal view definition
            tenant_id: Tenant ID for metrics
        
        Returns:
            Slack API response
        """
        try:
            response = await self.client.views_open(
                trigger_id=trigger_id,
                view=view,
            )

            slack_api_calls.labels(
                tenant_id=tenant_id,
                endpoint="views.open",
                status="success",
            ).inc()

            logger.info(
                "slack_modal_opened",
                tenant_id=tenant_id,
                view_id=response.get("view", {}).get("id"),
            )

            return response.data

        except SlackApiError as e:
            slack_api_errors.labels(
                tenant_id=tenant_id,
                error_type=e.response["error"],
            ).inc()

            logger.error(
                "slack_modal_open_failed",
                tenant_id=tenant_id,
                error=e.response["error"],
            )
            raise

    async def get_user_info(
        self,
        user_id: str,
        tenant_id: str = "unknown",
    ) -> dict[str, Any]:
        """
        Get user information.
        
        Args:
            user_id: Slack user ID
            tenant_id: Tenant ID for metrics
        
        Returns:
            User information
        """
        try:
            response = await self.client.users_info(user=user_id)

            slack_api_calls.labels(
                tenant_id=tenant_id,
                endpoint="users.info",
                status="success",
            ).inc()

            return response.data.get("user", {})

        except SlackApiError as e:
            slack_api_errors.labels(
                tenant_id=tenant_id,
                error_type=e.response["error"],
            ).inc()

            logger.warning(
                "slack_user_info_failed",
                user_id=user_id,
                tenant_id=tenant_id,
                error=e.response["error"],
            )
            return {}


# Global client instance
_slack_client_instance: Optional[SlackClient] = None


def get_slack_client() -> SlackClient:
    """Get or create the global Slack client instance."""
    global _slack_client_instance
    
    if _slack_client_instance is None:
        _slack_client_instance = SlackClient()
    
    return _slack_client_instance
