# app/kafka/consumer.py
"""Kafka consumer for processing messages"""

import asyncio
import json
from typing import Optional, Callable, Any
import structlog
from aiokafka import AIOKafkaConsumer

logger = structlog.get_logger()


def _deserialize_value(data: bytes) -> Optional[dict]:
    """Safely deserialize JSON message value."""
    if not data:
        return None
    try:
        return json.loads(data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.warning("message_deserialization_failed", error=str(e))
        return None


class KafkaMessageConsumer:
    """Kafka consumer for processing incoming messages"""
    
    def __init__(
        self,
        brokers: str,
        group_id: str,
        topic: str,
        message_handler: Callable[[dict], Any],
    ):
        """
        Initialize Kafka consumer
        
        Args:
            brokers: Kafka broker addresses (comma-separated)
            group_id: Consumer group ID
            topic: Topic to subscribe to
            message_handler: Async function to handle messages
        """
        self.brokers = brokers.split(",") if isinstance(brokers, str) else brokers
        self.group_id = group_id
        self.topic = topic
        self.message_handler = message_handler
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self) -> None:
        """Start consuming messages from Kafka"""
        try:
            logger.info(
                "kafka_consumer_starting",
                brokers=self.brokers,
                topic=self.topic,
                group_id=self.group_id,
            )
            
            self.consumer = AIOKafkaConsumer(
                self.topic,
                bootstrap_servers=self.brokers,
                group_id=self.group_id,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                max_poll_interval_ms=600000,  # 10 minutes to accommodate Gemini API calls
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
                value_deserializer=_deserialize_value,
            )
            
            await self.consumer.start()
            self._running = True
            logger.info("kafka_consumer_started", topic=self.topic)
            
            # Start consuming in the background
            self._task = asyncio.create_task(self._consume_messages())
            
        except Exception as e:
            logger.error("kafka_consumer_startup_failed", error=str(e))
            raise
    
    async def stop(self) -> None:
        """Stop consuming messages from Kafka"""
        try:
            self._running = False
            
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            
            if self.consumer:
                await self.consumer.stop()
            
            logger.info("kafka_consumer_stopped", topic=self.topic)
            
        except Exception as e:
            logger.error("kafka_consumer_stop_failed", error=str(e))
    
    async def _consume_messages(self) -> None:
        """Consume messages from Kafka"""
        try:
            logger.info("kafka_consumer_loop_starting", topic=self.topic)
            message_count = 0
            async for message in self.consumer:
                message_count += 1
                if not self._running:
                    break
                
                try:
                    logger.info(
                        "kafka_message_received",
                        topic=message.topic,
                        partition=message.partition,
                        offset=message.offset,
                        message_count=message_count,
                    )
                    
                    # Process the message if it was successfully deserialized
                    if message.value:
                        await self.message_handler(message.value)
                    else:
                        logger.warning("skipping_invalid_message", offset=message.offset)
                    
                except Exception as e:
                    logger.error(
                        "kafka_message_processing_failed",
                        error=str(e),
                        topic=message.topic,
                    )
                    # Continue processing other messages
        
        except asyncio.CancelledError:
            logger.info("kafka_consumer_cancelled")
        except Exception as e:
            logger.error("kafka_consumer_error", error=str(e))
            if self._running:
                # Attempt to restart after a delay
                await asyncio.sleep(5)
                await self.start()
