from typing import Any, Optional
from slack_sdk.errors import SlackApiError
from src.utils.observability import get_logger
from src.clients.slack_repository import SlackRepository

logger = get_logger(__name__)

class SlackClientRepository(SlackRepository):
    """Concrete implementation of SlackRepository."""

    def __init__(self, client: Any) -> None:
        """Initialize repository with a Slack client."""
        self.client = client

    async def post_message(
        self,
        channel: str,
        text: Optional[str] = None,
        blocks: Optional[list[dict[str, Any]]] = None,
        thread_ts: Optional[str] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Post a message to Slack."""
        try:
            response = await self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks,
                thread_ts=thread_ts,
                **kwargs,
            )
            return response.data
        except SlackApiError as e:
            logger.error(
                "slack_post_message_failed",
                channel=channel,
                error=e.response.get("error"),
            )
            raise

    async def update_message(
        self,
        channel: str,
        ts: str,
        text: Optional[str] = None,
        blocks: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Update a Slack message."""
        try:
            response = await self.client.chat_update(
                channel=channel,
                ts=ts,
                text=text,
                blocks=blocks,
                **kwargs,
            )
            return response.data
        except SlackApiError as e:
            logger.error(
                "slack_update_message_failed",
                channel=channel,
                ts=ts,
                error=e.response.get("error"),
            )
            raise

    async def add_reaction(
        self,
        channel: str,
        timestamp: str,
        emoji: str,
    ) -> dict[str, Any]:
        """Add a reaction to a message."""
        try:
            response = await self.client.reactions_add(
                channel=channel,
                timestamp=timestamp,
                name=emoji,
            )
            return response.data
        except SlackApiError as e:
            logger.error(
                "slack_add_reaction_failed",
                channel=channel,
                timestamp=timestamp,
                emoji=emoji,
                error=e.response.get("error"),
            )
            raise
