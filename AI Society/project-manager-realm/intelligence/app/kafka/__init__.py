# app/kafka/__init__.py
"""Kafka message processing module - Consumer, producer, and handlers."""

from app.kafka.implementations.consumer import KafkaMessageConsumer
from app.kafka.implementations.producer import KafkaMessageProducer
from app.kafka.implementations.handlers import handle_slack_message

__all__ = ["KafkaMessageConsumer", "KafkaMessageProducer", "handle_slack_message"]
