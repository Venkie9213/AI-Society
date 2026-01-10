from abc import ABC, abstractmethod
from typing import Any, Optional

class SlackRepository(ABC):
    """Abstract repository for Slack operations."""

    @abstractmethod
    async def post_message(
        self,
        channel: str,
        text: Optional[str] = None,
        blocks: Optional[list[dict[str, Any]]] = None,
        thread_ts: Optional[str] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Post a message to Slack."""
        pass

    @abstractmethod
    async def update_message(
        self,
        channel: str,
        ts: str,
        text: Optional[str] = None,
        blocks: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Update a Slack message."""
        pass

    @abstractmethod
    async def add_reaction(
        self,
        channel: str,
        timestamp: str,
        emoji: str,
    ) -> dict[str, Any]:
        """Add a reaction to a message."""
        pass
