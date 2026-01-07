"""Kafka event producer for publishing internal events."""

import json
from typing import Any, Optional

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from src.config import settings
from src.utils.observability import (
    get_logger,
    kafka_messages_published,
    kafka_publish_errors,
)

logger = get_logger(__name__)


class EventProducer:
    """Kafka event producer for publishing internal events."""

    def __init__(self) -> None:
        """Initialize the event producer."""
        self._producer: Optional[AIOKafkaProducer] = None

    async def start(self) -> None:
        """Start the Kafka producer."""
        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_servers_list,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                compression_type="gzip",
            )
            await self._producer.start()
            logger.info(
                "kafka_producer_started",
                bootstrap_servers=settings.kafka_bootstrap_servers,
            )
        except Exception as e:
            logger.error(
                "kafka_producer_start_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if self._producer:
            try:
                await self._producer.stop()
                logger.info("kafka_producer_stopped")
            except Exception as e:
                logger.error(
                    "kafka_producer_stop_failed",
                    error=str(e),
                )

    async def publish_event(
        self,
        topic: str,
        event: dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Publish an event to a Kafka topic.
        
        Args:
            topic: Topic name (without prefix)
            event: Event payload as dictionary
            key: Optional message key for partitioning
            headers: Optional message headers
        
        Raises:
            KafkaError: If publishing fails
        """
        if not self._producer:
            raise RuntimeError("Producer not started. Call start() first.")

        full_topic = settings.get_kafka_topic(topic)
        tenant_id = event.get("tenant_id", "unknown")

        try:
            # Convert headers to bytes
            kafka_headers = None
            if headers:
                kafka_headers = [
                    (k, v.encode("utf-8")) for k, v in headers.items()
                ]

            # Publish to Kafka
            result = await self._producer.send_and_wait(
                topic=full_topic,
                value=event,
                key=key,
                headers=kafka_headers,
            )

            # Update metrics
            kafka_messages_published.labels(
                tenant_id=tenant_id,
                topic=full_topic,
            ).inc()

            logger.info(
                "event_published",
                topic=full_topic,
                event_id=event.get("event_id"),
                tenant_id=tenant_id,
                partition=result.partition,
                offset=result.offset,
            )

        except KafkaError as e:
            kafka_publish_errors.labels(
                tenant_id=tenant_id,
                topic=full_topic,
                error_type=type(e).__name__,
            ).inc()

            logger.error(
                "event_publish_failed",
                topic=full_topic,
                event_id=event.get("event_id"),
                tenant_id=tenant_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    async def __aenter__(self) -> "EventProducer":
        """Context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Context manager exit."""
        await self.stop()


# Global producer instance
_producer_instance: Optional[EventProducer] = None


async def get_event_producer() -> EventProducer:
    """Get or create the global event producer instance."""
    global _producer_instance
    
    if _producer_instance is None:
        _producer_instance = EventProducer()
        await _producer_instance.start()
    
    return _producer_instance


async def shutdown_event_producer() -> None:
    """Shutdown the global event producer instance."""
    global _producer_instance
    
    if _producer_instance:
        await _producer_instance.stop()
        _producer_instance = None
