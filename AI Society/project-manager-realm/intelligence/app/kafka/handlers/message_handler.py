"""Simplified Kafka message handler using orchestrator pattern.

Delegates to MessageProcessingOrchestrator for actual processing.
"""

from typing import Dict, Any

import structlog

from app.message_processing import MessageProcessingOrchestrator

logger = structlog.get_logger()


async def handle_slack_message(
    message: Dict[str, Any],
    orchestrator: Any,  # AgentOrchestrator
    db_session: Any,  # AsyncSession
    producer: Any = None,  # KafkaMessageProducer
) -> None:
    """Handle Slack message received event.
    
    Simplified handler that delegates to MessageProcessingOrchestrator.
    
    Args:
        message: Kafka message payload with Slack message data
        orchestrator: Agent orchestrator instance
        db_session: Database session
        producer: Kafka producer for publishing responses
    """
    try:
        # Extract payload
        payload = message.get("payload", {})
        event_id = message.get("event_id")
        
        text = payload.get("text", "")
        slack_user_id = payload.get("slack_user_id", "")
        slack_channel_id = payload.get("slack_channel_id", "")
        slack_team_id = payload.get("slack_team_id", "")
        thread_ts = payload.get("thread_ts", "")
        message_ts = payload.get("message_ts", "")
        
        logger.info(
            "slack_message_received",
            event_id=event_id,
            channel=slack_channel_id,
            user=slack_user_id,
        )
        
        # Delegate to orchestrator
        processing_orchestrator = MessageProcessingOrchestrator(
            db_session=db_session,
            agent_orchestrator=orchestrator,
            producer=producer,
        )
        
        await processing_orchestrator.process_slack_message(
            text=text,
            slack_user_id=slack_user_id,
            slack_channel_id=slack_channel_id,
            slack_team_id=slack_team_id,
            thread_ts=thread_ts,
            message_ts=message_ts,
        )
        
        logger.info("slack_message_processed", event_id=event_id)
    
    except Exception as e:
        logger.error(
            "slack_message_processing_failed",
            event_id=message.get("event_id"),
            error=str(e),
            exc_info=True,
        )
        raise
