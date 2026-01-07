"""Correlation ID middleware for distributed tracing."""

import uuid
from typing import Callable

from fastapi import Request, Response

from src.utils.observability import add_context, clear_context, get_logger

logger = get_logger(__name__)

CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationMiddleware:
    """Middleware to handle correlation IDs for request tracing."""

    def __init__(self, app: Callable) -> None:
        """Initialize the middleware."""
        self.app = app

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Add or extract correlation ID from request."""
        # Get existing correlation ID or generate new one
        correlation_id = request.headers.get(CORRELATION_ID_HEADER)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Store in request state
        request.state.correlation_id = correlation_id

        # Add to logging context
        add_context(correlation_id=correlation_id)

        try:
            # Process request
            response = await call_next(request)

            # Add correlation ID to response headers
            response.headers[CORRELATION_ID_HEADER] = correlation_id

            return response

        finally:
            # Clean up logging context
            clear_context("correlation_id")


def get_correlation_id(request: Request) -> str:
    """
    Get correlation ID from request state.
    
    Args:
        request: FastAPI request object
    
    Returns:
        Correlation ID
    """
    return getattr(request.state, "correlation_id", "unknown")
