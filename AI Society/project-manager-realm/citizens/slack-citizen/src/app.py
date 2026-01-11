"""Application factory for the Slack Citizen service."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.routes import health_router, webhooks_router
from src.middleware.context import RequestContextMiddleware
from src.core.services import ServiceManager
from src.core.discovery import DiscoveryClient


def create_app() -> FastAPI:
    """Build and return the FastAPI application instance."""
    app = FastAPI(
        title="Slack Citizen",
        description="Bidirectional adapter between Slack and AI Society platform",
        version=settings.app_version,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add Context Middleware
    app.add_middleware(RequestContextMiddleware)

    # Initialize Service Manager
    service_manager = ServiceManager()
    discovery_client = DiscoveryClient()

    # Include routers
    app.include_router(health_router)
    app.include_router(webhooks_router)

    @app.on_event("startup")
    async def on_startup() -> None:
        await service_manager.start()
        await discovery_client.register()

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        await discovery_client.unregister()
        await service_manager.stop()

    return app
