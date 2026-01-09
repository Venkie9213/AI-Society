"""Application factory for the Slack Citizen service.

Creates and configures the FastAPI app, registers middleware, routers,
and lifecycle handlers. Keeps `src/main.py` minimal.
"""

import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.events import get_event_producer, shutdown_event_producer
from src.middleware import CorrelationMiddleware, SlackSignatureMiddleware, TenantMiddleware
from src.routes import health_router, webhooks_router
from src.utils.observability import get_logger, start_metrics_server
from src.services.slack_notifier import SlackNotifier
from src.services.internal_event_router import InternalEventRouter
from src.services.consumer import KafkaConsumerService

logger = get_logger(__name__)


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

    # Instantiate services
    notifier = SlackNotifier()
    router = InternalEventRouter(notifier)
    consumer_service = KafkaConsumerService(
        topics=[
            "requirement.requirement.created",
            "requirement.clarification.completed",
            "pulse.execution.failed",
            "reply.requested",
        ],
        handler=router.handle_event,
    )
    
    # NOTE: Topics are automatically prefixed with "project-manager." by get_kafka_topic()

    # Register middleware (order matters)
    app.middleware("http")(TenantMiddleware(app))
    app.middleware("http")(CorrelationMiddleware(app))
    app.middleware("http")(SlackSignatureMiddleware(app))

    # Include routers
    app.include_router(health_router)
    app.include_router(webhooks_router)

    @app.on_event("startup")
    async def on_startup() -> None:
        logger.info(
            "starting_slack_citizen",
            version=settings.app_version,
            environment=settings.environment,
        )
        start_metrics_server()
        await get_event_producer()
        if settings.environment != "test":
            await consumer_service.start()
        logger.info("slack_citizen_started")

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        logger.info("shutting_down_slack_citizen")
        if settings.environment != "test":
            await consumer_service.stop()
        await shutdown_event_producer()
        logger.info("slack_citizen_stopped")

    return app
