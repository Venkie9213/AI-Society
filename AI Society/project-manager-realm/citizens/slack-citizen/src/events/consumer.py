"""Kafka event consumer for subscribing to internal events."""

import asyncio
import json
from typing import Any, Callable, Coroutine, Optional

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from src.config import settings
from src.utils.observability import (
    event_processing_duration,
    get_logger,
    kafka_messages_consumed,
)

logger = get_logger(__name__)


class EventConsumer:
    """Kafka event consumer for subscribing to internal events."""

    def __init__(
        self,
        topics: list[str],
        handler: Callable[[dict[str, Any]], Coroutine[Any, Any, None]],
        group_id: Optional[str] = None,
    ) -> None:
        """
        Initialize the event consumer.
        
        Args:
            topics: List of topic names (without prefix) to subscribe to
            handler: Async function to handle consumed events
            group_id: Consumer group ID (defaults to settings)
        """
        self.topics = [settings.get_kafka_topic(t) for t in topics]
        self.handler = handler
        self.group_id = group_id or settings.kafka_consumer_group_id
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._running = False

    async def start(self) -> None:
        """Start the Kafka consumer."""
        try:
            self._consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=settings.kafka_servers_list,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                key_deserializer=lambda k: k.decode("utf-8") if k else None,
                auto_offset_reset="earliest",
                enable_auto_commit=False,  # Manual commit for exactly-once
                max_poll_records=10,
                session_timeout_ms=30000,
            )
            await self._consumer.start()
            self._running = True
            
            logger.info(
                "kafka_consumer_started",
                topics=self.topics,
                group_id=self.group_id,
            )
        except Exception as e:
            logger.error(
                "kafka_consumer_start_failed",
                topics=self.topics,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    async def stop(self) -> None:
        """Stop the Kafka consumer."""
        self._running = False
        
        if self._consumer:
            try:
                await self._consumer.stop()
                logger.info("kafka_consumer_stopped")
            except Exception as e:
                logger.error(
                    "kafka_consumer_stop_failed",
                    error=str(e),
                )

    async def consume(self) -> None:
        """
        Start consuming messages from Kafka topics.
        
        This method runs indefinitely until stop() is called.
        """
        if not self._consumer:
            raise RuntimeError("Consumer not started. Call start() first.")

        logger.info("kafka_consumer_polling", topics=self.topics)

        while self._running:
            try:
                # Poll for messages
                result = await self._consumer.getmany(timeout_ms=1000)
                
                for topic_partition, messages in result.items():
                    for message in messages:
                        try:
                            await self._process_message(
                                message.value,
                                topic_partition.topic,
                            )
                            
                            # Commit offset after successful processing
                            await self._consumer.commit()
                            
                        except Exception as e:
                            logger.error(
                                "message_processing_failed",
                                topic=topic_partition.topic,
                                partition=topic_partition.partition,
                                offset=message.offset,
                                error=str(e),
                                error_type=type(e).__name__,
                            )
                            # Don't commit on error - message will be reprocessed

            except KafkaError as e:
                logger.error(
                    "kafka_consume_error",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                await asyncio.sleep(5)  # Back off on error
            except Exception as e:
                logger.error(
                    "unexpected_consume_error",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                await asyncio.sleep(5)

    async def _process_message(self, event: dict[str, Any], topic: str) -> None:
        """
        Process a single message.
        
        Args:
            event: Event payload
            topic: Topic name
        """
        tenant_id = event.get("tenant_id", "unknown")
        event_type = event.get("payload", {}).get("__type__", "unknown")
        
        logger.debug(
            "processing_message",
            topic=topic,
            event_id=event.get("event_id"),
            tenant_id=tenant_id,
            event_type=event_type,
        )

        # Track metrics
        kafka_messages_consumed.labels(
            tenant_id=tenant_id,
            topic=topic,
        ).inc()

        # Process with timing
        with event_processing_duration.labels(
            tenant_id=tenant_id,
            event_type=event_type,
        ).time():
            await self.handler(event)

        logger.info(
            "message_processed",
            topic=topic,
            event_id=event.get("event_id"),
            tenant_id=tenant_id,
        )

    async def run(self) -> None:
        """Start the consumer and begin consuming messages."""
        await self.start()
        try:
            await self.consume()
        finally:
            await self.stop()

    async def __aenter__(self) -> "EventConsumer":
        """Context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Context manager exit."""
        await self.stop()
