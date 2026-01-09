"""Kafka message handlers.

Handlers are simplified and delegate to domain-specific orchestrators.
"""

from app.kafka.handlers.message_handler import handle_slack_message

__all__ = ["handle_slack_message"]
