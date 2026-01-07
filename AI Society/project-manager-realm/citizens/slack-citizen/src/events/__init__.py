"""Events module initialization."""

from src.events.consumer import EventConsumer
from src.events.producer import (
    EventProducer,
    get_event_producer,
    shutdown_event_producer,
)

__all__ = [
    "EventProducer",
    "EventConsumer",
    "get_event_producer",
    "shutdown_event_producer",
]
