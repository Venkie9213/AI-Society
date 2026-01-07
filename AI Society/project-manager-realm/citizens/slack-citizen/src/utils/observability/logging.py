"""Structured logging configuration."""

import logging
import sys
from contextvars import ContextVar
from typing import Any, Optional

import structlog

from src.config import settings

# Context variables for correlation and tenant IDs
correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)
tenant_id_var: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)


def configure_logging() -> None:
    """Configure structured logging with structlog."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
            if not settings.is_development
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger with the given name."""
    return structlog.get_logger(name)


def add_context(**kwargs: Any) -> None:
    """Add context to all subsequent log messages."""
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context(*keys: str) -> None:
    """Clear specific context keys."""
    structlog.contextvars.unbind_contextvars(*keys)
