from fastapi import Request
from src.config import settings

def get_tenant_id(request: Request) -> str:
    """Get tenant ID from request state, defaulting to settings if not found."""
    return getattr(request.state, "tenant_id", settings.default_tenant_id)

def get_correlation_id(request: Request) -> str:
    """Get correlation ID from request state, defaulting to 'unknown' if not found."""
    return getattr(request.state, "correlation_id", "unknown")
