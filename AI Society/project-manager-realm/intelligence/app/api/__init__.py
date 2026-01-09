# app/api/__init__.py
"""API routers and endpoints

Organized modules:
- endpoints/: API route handlers
  - agents: Agent execution endpoints
  - providers: Provider management endpoints
  - health: Health check endpoints
  - debug: Debug utility endpoints
- schemas/: Data models
  - dtos/: Data Transfer Objects for API layer
"""

from app.api.endpoints import (
    agents_router,
    providers_router,
    health_router,
    debug_router,
)

__all__ = [
    "endpoints",
    "schemas",
    "agents_router",
    "providers_router",
    "health_router",
    "debug_router",
]
