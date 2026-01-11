import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bound_contextvars
from src.config import settings

class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to manage tenant and correlation IDs in the request context."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip for health/metrics
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        tenant_id = request.headers.get("X-Tenant-ID", settings.default_tenant_id)
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        request.state.tenant_id = tenant_id
        request.state.correlation_id = correlation_id

        with bound_contextvars(tenant_id=tenant_id, correlation_id=correlation_id):
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response
