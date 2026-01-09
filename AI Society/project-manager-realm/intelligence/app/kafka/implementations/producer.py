"""Kafka producer for publishing messages"""

import json
from typing import Dict, Any, Optional
import uuid
import structlog
from aiokafka import AIOKafkaProducer
from datetime import datetime, timezone

logger = structlog.get_logger()


class KafkaMessageProducer:
    """Kafka producer for publishing messages to topics"""
    
    def __init__(self, brokers: str):
        """
        Initialize Kafka producer
        
        Args:
            brokers: Kafka broker addresses (comma-separated)
        """
        self.brokers = brokers.split(",") if isinstance(brokers, str) else brokers
        self.producer: Optional[AIOKafkaProducer] = None
    
    async def start(self) -> None:
        """Start the Kafka producer"""
        try:
            logger.info("kafka_producer_starting", brokers=self.brokers)
            
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.brokers,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            )
            
            await self.producer.start()
            logger.info("kafka_producer_started")
        except Exception as e:
            logger.error("kafka_producer_startup_failed", error=str(e))
            raise
    
    async def stop(self) -> None:
        """Stop the Kafka producer"""
        try:
            if self.producer:
                await self.producer.stop()
            logger.info("kafka_producer_stopped")
        except Exception as e:
            logger.error("kafka_producer_stop_failed", error=str(e))
    
    async def publish_slack_reply(
        self,
        channel_id: str,
        thread_ts: str,
        message_text: str,
        message_blocks: Optional[list] = None,
    ) -> None:
        """
        Publish a Slack reply message to be sent by Slack Citizen
        
        Args:
            channel_id: Slack channel ID
            thread_ts: Thread timestamp (for replies in thread)
            message_text: Text content of the message
            message_blocks: Optional Slack block kit blocks for rich formatting
        """
        if not self.producer:
            logger.warning("producer_not_initialized", operation="publish_slack_reply")
            return
        
        try:
            
            message = {
                "event_id": str(uuid.uuid4()),
                "event_type": "slack.reply.requested",
                "source": "intelligence-service",
                "occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "payload": {
                    "slack_channel_id": channel_id,
                    "slack_thread_ts": thread_ts,
                    "message_text": message_text,
                    "blocks": message_blocks or [],
                },
            }
            
            await self.producer.send_and_wait(
                "project-manager.reply.requested",
                value=message,
            )
            
            logger.info(
                "slack_reply_published",
                channel_id=channel_id,
                thread_ts=thread_ts,
            )
        except Exception as e:
            logger.error(
                "slack_reply_publish_failed",
                error=str(e),
                channel_id=channel_id,
            )
