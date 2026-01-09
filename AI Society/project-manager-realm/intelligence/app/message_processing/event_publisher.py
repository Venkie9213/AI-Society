"""Event publishing abstraction layer.

Handles publishing events to Kafka topics with proper serialization.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

import structlog

logger = structlog.get_logger()


class Event:
    """Base event model."""
    
    def __init__(
        self,
        event_id: Optional[str] = None,
        event_type: str = "",
        source: str = "intelligence-service",
        payload: Optional[Dict[str, Any]] = None,
    ):
        self.event_id = event_id or str(uuid.uuid4())
        self.event_type = event_type
        self.source = source
        self.payload = payload or {}
        self.occurred_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for Kafka publishing."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "occurred_at": self.occurred_at,
            "payload": self.payload,
        }


class ClarificationCompletedEvent(Event):
    """Event published when clarification phase completes."""
    
    def __init__(
        self,
        conversation_id: str,
        slack_channel_id: str,
        slack_thread_ts: str,
        questions: List[Dict[str, Any]],
        rationale: str,
        confidence_score: float,
        is_completed: bool = False,
    ):
        super().__init__(
            event_type="requirement.clarification.completed",
            payload={
                "conversation_id": conversation_id,
                "slack_channel_id": slack_channel_id,
                "slack_thread_ts": slack_thread_ts,
                "questions": questions,
                "rationale": rationale,
                "confidence_score": confidence_score,
                "is_completed": is_completed,
            }
        )


class EventPublisher:
    """Publishes events to Kafka with error handling.
    
    Single Responsibility: Publishing events to Kafka topics.
    """
    
    CONFIDENCE_THRESHOLD = 95.0
    
    def __init__(self, producer: Any):  # KafkaMessageProducer
        self.producer = producer
    
    async def publish_clarification_event(
        self,
        conversation_id: str,
        slack_channel_id: str,
        slack_thread_ts: str,
        questions: List[Dict[str, Any]],
        rationale: str,
        confidence_score: float,
    ) -> bool:
        """Publish clarification questions event."""
        try:
            is_completed = confidence_score >= self.CONFIDENCE_THRESHOLD
            
            event = ClarificationCompletedEvent(
                conversation_id=conversation_id,
                slack_channel_id=slack_channel_id,
                slack_thread_ts=slack_thread_ts,
                questions=questions,
                rationale=rationale,
                confidence_score=confidence_score,
                is_completed=is_completed,
            )
            
            await self.producer.producer.send_and_wait(
                "project-manager.requirement.clarification.completed",
                value=event.to_dict(),
            )
            
            logger.info(
                "event_published",
                event_type=event.event_type,
                conversation_id=conversation_id,
                is_completed=is_completed,
                confidence=confidence_score,
            )
            return True
        except Exception as e:
            logger.error(
                "event_publish_failed",
                event_type="requirement.clarification.completed",
                error=str(e),
            )
            return False
