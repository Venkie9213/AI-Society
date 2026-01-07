"""Internal event router using Chain of Responsibility pattern."""

from typing import Any

from src.services.event_router_chain import EventRouterChain
from src.utils.observability import get_logger

logger = get_logger(__name__)


class InternalEventRouter:
    """Routes internal Kafka events to appropriate handlers.

    Uses Chain of Responsibility pattern to decouple event handling.
    """

    def __init__(self, notifier=None) -> None:
        """Initialize the router.

        Args:
            notifier: Optional SlackNotifier (for backward compatibility)
        """
        self._notifier = notifier  # Kept for backward compatibility
        self._chain = EventRouterChain()

    async def handle_event(self, event: dict[str, Any]) -> None:
        """Entry point for the EventConsumer."""
        try:
            event_id = event.get("event_id", "unknown")
            source = event.get("source", "unknown")

            logger.debug(
                "handling_internal_event",
                event_id=event_id,
                source=source,
                tenant_id=event.get("tenant_id"),
            )

            # Route through the chain
            await self._chain.route_event(event)

        except Exception as e:
            logger.error(
                "internal_event_handling_failed",
                event_id=event.get("event_id", "unknown"),
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
