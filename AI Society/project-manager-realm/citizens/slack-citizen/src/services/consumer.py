"""Kafka consumer service for managing event consumption (Service Layer)."""

import asyncio
from typing import Any, Callable, Coroutine, List, Optional

from src.config import settings
from src.events import EventConsumer
from src.utils.observability import get_logger

logger = get_logger(__name__)


class KafkaConsumerService:
    """Service for managing Kafka event consumption lifecycle.

    Wraps EventConsumer with dependency injection and lifecycle management.
    Follows Dependency Injection pattern for testability.
    """

    def __init__(
        self,
        topics: List[str],
        handler: Callable[[dict[str, Any]], Coroutine[Any, Any, None]],
        group_id: Optional[str] = None,
    ) -> None:
        """
        Initialize the Kafka consumer service.

        Args:
            topics: List of topic names to subscribe to
            handler: Async function to handle consumed events
            group_id: Consumer group ID (defaults to settings)
        """
        self._topics = topics
        self._handler = handler
        self._group_id = group_id or settings.kafka_consumer_group_id
        self._task: Optional[asyncio.Task] = None
        self._consumer: Optional[EventConsumer] = None

    async def start(self) -> None:
        """Start the Kafka consumer in background task."""
        if self._task:
            logger.warning("kafka_consumer_already_running")
            return

        self._consumer = EventConsumer(
            topics=self._topics,
            handler=self._handler,
            group_id=self._group_id,
        )
        self._task = asyncio.create_task(self._consumer.run())

        logger.info(
            "kafka_consumer_service_started",
            topics=self._topics,
            group_id=self._group_id,
        )

    async def stop(self) -> None:
        """Stop the Kafka consumer."""
        logger.info("stopping_kafka_consumer_service")

        if self._consumer:
            await self._consumer.stop()

        if self._task:
            try:
                self._task.cancel()
                await self._task
            except asyncio.CancelledError:
                logger.debug("kafka_consumer_task_cancelled")
            except Exception as e:
                logger.error(
                    "error_stopping_kafka_consumer_task",
                    error=str(e),
                )

    async def is_running(self) -> bool:
        """Check if consumer task is running."""
        if not self._task:
            return False
        return not self._task.done()
