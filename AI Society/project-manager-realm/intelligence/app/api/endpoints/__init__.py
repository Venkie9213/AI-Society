"""API endpoint modules."""

from app.api.endpoints.agents import router as agents_router
from app.api.endpoints.providers import router as providers_router
from app.api.endpoints.health import router as health_router
from app.api.endpoints.debug import router as debug_router

__all__ = [
    "agents_router",
    "providers_router",
    "health_router",
    "debug_router",
]
