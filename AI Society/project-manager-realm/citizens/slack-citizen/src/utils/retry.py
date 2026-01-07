"""Retry utilities with exponential backoff and Dead Letter Queue support."""

import asyncio
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, cast

from tenacity import (
    AsyncRetrying,
    RetryError,
    stop_after_attempt,
    wait_exponential,
)

from src.config import settings
from src.utils.observability import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""

    pass


async def publish_to_dlq(
    topic: str,
    message: dict[str, Any],
    error: Exception,
    tenant_id: str,
) -> None:
    """Publish failed message to Dead Letter Queue."""
    from src.events.producer import get_event_producer

    dlq_topic = settings.get_dlq_topic(topic)
    dlq_message = {
        "original_topic": topic,
        "original_message": message,
        "error": str(error),
        "error_type": type(error).__name__,
        "tenant_id": tenant_id,
    }

    try:
        producer = await get_event_producer()
        await producer.publish_event(
            topic=dlq_topic,
            event=dlq_message,
            key=message.get("event_id", ""),
        )
        logger.warning(
            "message_published_to_dlq",
            tenant_id=tenant_id,
            original_topic=topic,
            dlq_topic=dlq_topic,
            error_type=type(error).__name__,
        )
    except Exception as dlq_error:
        logger.error(
            "failed_to_publish_to_dlq",
            tenant_id=tenant_id,
            original_topic=topic,
            dlq_topic=dlq_topic,
            error=str(dlq_error),
        )


def retry_with_dlq(
    max_attempts: Optional[int] = None,
    base_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    dlq_topic: Optional[str] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying async functions with exponential backoff.
    
    On final failure, publishes the message to a Dead Letter Queue.
    
    Args:
        max_attempts: Maximum retry attempts (default from settings)
        base_delay: Base delay in seconds (default from settings)
        max_delay: Maximum delay in seconds (default from settings)
        dlq_topic: Topic to publish failed messages to (required for DLQ)
    """
    max_attempts = max_attempts or settings.max_retry_attempts
    base_delay = base_delay or settings.retry_base_delay_seconds
    max_delay = max_delay or settings.retry_max_delay_seconds

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            tenant_id = kwargs.get("tenant_id", "unknown")
            
            try:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(max_attempts),
                    wait=wait_exponential(
                        multiplier=base_delay,
                        max=max_delay,
                    ),
                    reraise=True,
                ):
                    with attempt:
                        logger.debug(
                            "retry_attempt",
                            function=func.__name__,
                            attempt_number=attempt.retry_state.attempt_number,
                            tenant_id=tenant_id,
                        )
                        result = await func(*args, **kwargs)
                        return cast(T, result)
            except RetryError as e:
                logger.error(
                    "retry_exhausted",
                    function=func.__name__,
                    max_attempts=max_attempts,
                    tenant_id=tenant_id,
                    error=str(e),
                )
                
                # Publish to DLQ if topic is specified
                if dlq_topic:
                    message = kwargs.get("message") or kwargs.get("event", {})
                    if message:
                        await publish_to_dlq(
                            topic=dlq_topic,
                            message=message,
                            error=e,
                            tenant_id=tenant_id,
                        )
                
                raise RetryExhaustedError(
                    f"Function {func.__name__} failed after {max_attempts} attempts"
                ) from e

        return cast(Callable[..., T], wrapper)

    return decorator


async def retry_async(
    func: Callable[..., T],
    *args: Any,
    max_attempts: Optional[int] = None,
    base_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    **kwargs: Any,
) -> T:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_attempts: Maximum retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        *args, **kwargs: Arguments to pass to the function
    
    Returns:
        Result of the function call
    """
    max_attempts = max_attempts or settings.max_retry_attempts
    base_delay = base_delay or settings.retry_base_delay_seconds
    max_delay = max_delay or settings.retry_max_delay_seconds

    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=base_delay, max=max_delay),
        reraise=True,
    ):
        with attempt:
            result = await func(*args, **kwargs)
            return cast(T, result)

    # This should never be reached due to reraise=True
    raise RuntimeError("Unexpected retry completion")
