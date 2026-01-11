import json
import asyncio
from aiokafka import AIOKafkaConsumer
from src.config.settings import settings
from src.utils.observability import get_logger
from typing import Callable, Optional

logger = get_logger(__name__)

class KafkaConsumerService:
    """Consumes messages from Kafka and routes them to handlers."""
    
    def __init__(self, topics: list[str], handler: Callable):
        self.topics = topics
        self.handler = handler
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.is_running = False
        
    async def start(self):
        """Start the Kafka consumer."""
        self.consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=settings.kafka_brokers,
            group_id=settings.kafka_consumer_group,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
        )
        
        await self.consumer.start()
        self.is_running = True
        logger.info("kafka_consumer_started", topics=self.topics, group_id=settings.kafka_consumer_group)
        
        asyncio.create_task(self._consume_loop())
        
    async def _consume_loop(self):
        """Main consumption loop."""
        try:
            async for msg in self.consumer:
                if not self.is_running:
                    break
                    
                logger.info("kafka_message_received", topic=msg.topic, partition=msg.partition, offset=msg.offset)
                
                try:
                    await self.handler(msg)
                except Exception as e:
                    logger.error("kafka_message_handler_failed", error=str(e), topic=msg.topic)
                    
        except Exception as e:
            logger.error("kafka_consume_loop_error", error=str(e))
        finally:
            await self.stop()
            
    async def stop(self):
        """Stop the Kafka consumer."""
        self.is_running = False
        if self.consumer:
            await self.consumer.stop()
        logger.info("kafka_consumer_stopped")
