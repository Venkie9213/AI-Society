"""Event routing with Chain of Responsibility pattern."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from src.utils.observability import get_logger

logger = get_logger(__name__)


class EventHandler(ABC):
    """Abstract handler in the chain of responsibility."""

    def __init__(self):
        """Initialize the handler."""
        self._next_handler: Optional[EventHandler] = None

    def set_next(self, handler: "EventHandler") -> "EventHandler":
        """Set the next handler in the chain."""
        self._next_handler = handler
        return handler

    async def handle(self, event: dict[str, Any]) -> bool:
        """
        Handle the event.

        Returns True if handled, False otherwise.
        """
        if await self._can_handle(event):
            return await self._do_handle(event)

        if self._next_handler:
            return await self._next_handler.handle(event)

        return False

    @abstractmethod
    async def _can_handle(self, event: dict[str, Any]) -> bool:
        """Check if this handler can handle the event."""
        pass

    @abstractmethod
    async def _do_handle(self, event: dict[str, Any]) -> bool:
        """Handle the event."""
        pass


class RequirementEventHandler(EventHandler):
    """Handles requirement-related events."""

    async def _can_handle(self, event: dict[str, Any]) -> bool:
        """Check if event is from requirement service."""
        return event.get("source") == "requirement-service"

    async def _do_handle(self, event: dict[str, Any]) -> bool:
        """Route to appropriate requirement handler."""
        from src.services.slack_notifier import SlackNotifier

        notifier = SlackNotifier()
        payload = event.get("payload", {})

        if "requirement_id" in payload and "title" in payload:
            await notifier.notify_requirement_created(payload, event.get("tenant_id"))
            logger.debug(
                "requirement_created_handled",
                event_id=event.get("event_id"),
            )
            return True

        if "prd_content" in payload:
            await notifier.notify_clarification_completed(
                payload, event.get("tenant_id")
            )
            logger.debug(
                "clarification_completed_handled",
                event_id=event.get("event_id"),
            )
            return True

        return False


class PulseEventHandler(EventHandler):
    """Handles pulse-related events."""

    async def _can_handle(self, event: dict[str, Any]) -> bool:
        """Check if event is from pulse service."""
        return event.get("source", "").startswith("pulse")

    async def _do_handle(self, event: dict[str, Any]) -> bool:
        """Route to appropriate pulse handler."""
        from src.services.slack_notifier import SlackNotifier

        notifier = SlackNotifier()
        payload = event.get("payload", {})

        if "pulse_id" in payload and "error_message" in payload:
            await notifier.notify_pulse_failure(payload, event.get("tenant_id"))
            logger.debug(
                "pulse_failure_handled",
                event_id=event.get("event_id"),
            )
            return True

        return False


class ClarificationCompletedHandler(EventHandler):
    """Handles clarification completed events from intelligence service."""

    async def _can_handle(self, event: dict[str, Any]) -> bool:
        """Check if event is clarification completed."""
        return event.get("event_type") == "requirement.clarification.completed"

    async def _do_handle(self, event: dict[str, Any]) -> bool:
        """Handle clarification completed - format and send to Slack."""
        from src.services.slack_notifier import SlackNotifier
        from src.utils.slack_formatter import format_clarification_questions_for_slack

        notifier = SlackNotifier()
        payload = event.get("payload", {})

        if "questions" in payload and "slack_channel_id" in payload:
            # Format questions for Slack
            questions = payload.get("questions", [])
            rationale = payload.get("rationale", "")
            
            message_text, message_blocks = format_clarification_questions_for_slack(questions, rationale)
            
            # Send formatted message to Slack
            formatted_payload = {
                "slack_channel_id": payload.get("slack_channel_id"),
                "slack_thread_ts": payload.get("slack_thread_ts"),
                "message_text": message_text,
                "blocks": message_blocks,
            }
            
            await notifier.send_slack_reply(formatted_payload, event.get("tenant_id"))
            logger.debug(
                "clarification_completed_handled",
                event_id=event.get("event_id"),
            )
            return True

        return False


class IntelligenceEventHandler(EventHandler):
    """Handles intelligence service events."""

    async def _can_handle(self, event: dict[str, Any]) -> bool:
        """Check if event is from intelligence service."""
        return event.get("source") == "intelligence-service"

    async def _do_handle(self, event: dict[str, Any]) -> bool:
        """Handle intelligence service events."""
        from src.services.slack_notifier import SlackNotifier

        notifier = SlackNotifier()
        payload = event.get("payload", {})

        if "message_text" in payload and "slack_channel_id" in payload:
            await notifier.send_slack_reply(payload, event.get("tenant_id"))
            logger.debug(
                "slack_reply_handled",
                event_id=event.get("event_id"),
            )
            return True

        return False


class EventRouterChain:
    """Coordinates event routing chain."""

    def __init__(self):
        """Initialize the event router with handler chain."""
        # Build the chain of responsibility
        self.root_handler = RequirementEventHandler()
        clarification_handler = ClarificationCompletedHandler()
        pulse_handler = PulseEventHandler()
        intelligence_handler = IntelligenceEventHandler()

        self.root_handler.set_next(clarification_handler).set_next(pulse_handler).set_next(intelligence_handler)

    async def route_event(self, event: dict[str, Any]) -> None:
        """Route an event through the handler chain."""
        handled = await self.root_handler.handle(event)

        if not handled:
            logger.debug(
                "unhandled_event",
                event_id=event.get("event_id"),
                source=event.get("source"),
            )
