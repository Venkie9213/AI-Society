"""Main FastAPI application for Slack Citizen service."""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.clients import get_slack_client
from src.config import settings
from src.events import EventConsumer, get_event_producer, shutdown_event_producer
from src.middleware import (
    CorrelationMiddleware,
    SlackSignatureMiddleware,
    TenantMiddleware,
)
from src.routes import health_router, webhooks_router
from src.schemas import (
    EventEnvelope,
    PulseExecutionFailedPayload,
    RequirementClarificationCompletedPayload,
    RequirementCreatedPayload,
    SlackReplyRequestedPayload,
)
from src.utils.mapping import extract_slack_metadata_from_event
from src.utils.observability import configure_logging, get_logger, start_metrics_server

# Configure logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown tasks.
    """
    # Startup
    logger.info(
        "starting_slack_citizen",
        version=settings.app_version,
        environment=settings.environment,
    )

    # Start metrics server
    start_metrics_server()

    # Initialize Kafka producer
    await get_event_producer()

    # Start event consumer in background
    consumer_task = None
    if settings.environment != "test":
        consumer = EventConsumer(
            topics=[
                "requirement.requirement.created",
                "requirement.clarification.completed",
                "pulse.execution.failed",
                "slack.reply.requested",  # From Intelligence Service
            ],
            handler=handle_internal_event,
        )
        consumer_task = asyncio.create_task(consumer.run())

    logger.info("slack_citizen_started")

    yield

    # Shutdown
    logger.info("shutting_down_slack_citizen")

    # Stop consumer
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

    # Shutdown producer
    await shutdown_event_producer()

    logger.info("slack_citizen_stopped")


# Create FastAPI application
app = FastAPI(
    title="Slack Citizen",
    description="Bidirectional adapter between Slack and AI Society platform",
    version=settings.app_version,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware (order matters - executed bottom to top)
app.middleware("http")(TenantMiddleware(app))
app.middleware("http")(CorrelationMiddleware(app))
app.middleware("http")(SlackSignatureMiddleware(app))

# Include routers
app.include_router(health_router)
app.include_router(webhooks_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Any, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path if hasattr(request, "url") else "unknown",
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.is_development else "An error occurred",
        },
    )


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with service information."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }


async def handle_internal_event(event: dict[str, Any]) -> None:
    """
    Handle internal events consumed from Kafka.
    
    This function routes events to appropriate handlers based on the source
    and event type.
    
    Args:
        event: Internal event envelope
    """
    try:
        envelope = EventEnvelope(**event)
        source = envelope.source
        payload = envelope.payload
        
        logger.debug(
            "handling_internal_event",
            event_id=envelope.event_id,
            source=source,
            tenant_id=envelope.tenant_id,
        )

        # Route based on source
        if source == "requirement-service":
            await handle_requirement_event(envelope)
        elif source.startswith("pulse"):
            await handle_pulse_event(envelope)
        elif source == "intelligence-service":
            await handle_intelligence_event(envelope)
        else:
            logger.debug(
                "unhandled_event_source",
                source=source,
                event_id=envelope.event_id,
            )

    except Exception as e:
        logger.error(
            "internal_event_handling_failed",
            event_id=event.get("event_id"),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise


async def handle_requirement_event(envelope: EventEnvelope) -> None:
    """
    Handle requirement-related events.
    
    Args:
        envelope: Event envelope
    """
    payload = envelope.payload
    
    # Check if this is a requirement.created event
    if "requirement_id" in payload and "title" in payload:
        requirement = RequirementCreatedPayload(**payload)
        await notify_requirement_created(requirement, envelope.tenant_id)
    
    # Check if this is a clarification.completed event
    elif "prd_content" in payload:
        clarification = RequirementClarificationCompletedPayload(**payload)
        await notify_clarification_completed(clarification, envelope.tenant_id)


async def handle_pulse_event(envelope: EventEnvelope) -> None:
    """
    Handle pulse-related events.
    
    Args:
        envelope: Event envelope
    """
    payload = envelope.payload
    
    # Check if this is a pulse.execution.failed event
    if "pulse_id" in payload and "error_message" in payload:
        pulse_failure = PulseExecutionFailedPayload(**payload)
        await notify_pulse_failure(pulse_failure, envelope.tenant_id)


async def notify_requirement_created(
    requirement: RequirementCreatedPayload,
    tenant_id: str,
) -> None:
    """
    Notify Slack about a new requirement.
    
    Args:
        requirement: Requirement payload
        tenant_id: Tenant ID
    """
    slack_client = get_slack_client()
    
    # Extract Slack metadata
    channel_id = requirement.metadata.get("slack_channel_id")
    thread_ts = requirement.metadata.get("slack_thread_ts")
    
    if not channel_id:
        logger.warning(
            "no_slack_channel_for_requirement",
            requirement_id=requirement.requirement_id,
            tenant_id=tenant_id,
        )
        return

    # Post notification
    await slack_client.post_message(
        channel=channel_id,
        text=f"✅ Requirement created: {requirement.title}",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*New Requirement Created*\n\n*Title:* {requirement.title}\n*ID:* `{requirement.requirement_id}`",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{requirement.description}",
                },
            },
        ],
        thread_ts=thread_ts,
        tenant_id=tenant_id,
    )

    logger.info(
        "requirement_notification_sent",
        requirement_id=requirement.requirement_id,
        tenant_id=tenant_id,
        channel=channel_id,
    )


async def notify_clarification_completed(
    clarification: RequirementClarificationCompletedPayload,
    tenant_id: str,
) -> None:
    """
    Notify Slack about completed requirement clarification.
    
    Args:
        clarification: Clarification payload
        tenant_id: Tenant ID
    """
    slack_client = get_slack_client()
    
    # Extract Slack metadata
    channel_id = clarification.metadata.get("slack_channel_id")
    thread_ts = clarification.metadata.get("slack_thread_ts")
    
    if not channel_id:
        logger.warning(
            "no_slack_channel_for_clarification",
            requirement_id=clarification.requirement_id,
            tenant_id=tenant_id,
        )
        return

    # Post PRD to Slack
    await slack_client.post_message(
        channel=channel_id,
        text=f"📋 PRD completed for requirement {clarification.requirement_id}",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Product Requirements Document*",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:* {clarification.clarification_summary}",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*PRD:*\n```\n{clarification.prd_content[:2000]}\n```",
                },
            },
        ],
        thread_ts=thread_ts,
        tenant_id=tenant_id,
    )

    logger.info(
        "clarification_notification_sent",
        requirement_id=clarification.requirement_id,
        tenant_id=tenant_id,
        channel=channel_id,
    )


async def notify_pulse_failure(
    pulse_failure: PulseExecutionFailedPayload,
    tenant_id: str,
) -> None:
    """
    Notify Slack about pulse execution failure.
    
    Args:
        pulse_failure: Pulse failure payload
        tenant_id: Tenant ID
    """
    slack_client = get_slack_client()
    
    # Extract Slack metadata (if available)
    channel_id = pulse_failure.metadata.get("slack_channel_id")
    
    if not channel_id:
        # Use a default alerts channel or skip
        logger.warning(
            "no_slack_channel_for_pulse_failure",
            pulse_id=pulse_failure.pulse_id,
            tenant_id=tenant_id,
        )
        return

    # Post alert
    await slack_client.post_message(
        channel=channel_id,
        text=f"❌ Pulse execution failed: {pulse_failure.pulse_name}",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*⚠️ Pulse Execution Failed*\n\n*Pulse:* {pulse_failure.pulse_name}\n*Execution ID:* `{pulse_failure.execution_id}`",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Error:* {pulse_failure.error_message}",
                },
            },
        ],
        tenant_id=tenant_id,
    )

    logger.info(
        "pulse_failure_notification_sent",
        pulse_id=pulse_failure.pulse_id,
        tenant_id=tenant_id,
    )


async def handle_intelligence_event(envelope: EventEnvelope) -> None:
    """
    Handle intelligence-related events.
    
    Args:
        envelope: Event envelope
    """
    payload = envelope.payload
    
    # Check if this is a slack.reply.requested event
    if "message_text" in payload and "slack_channel_id" in payload:
        reply = SlackReplyRequestedPayload(**payload)
        await send_slack_reply(reply, envelope.tenant_id)


async def send_slack_reply(
    reply: SlackReplyRequestedPayload,
    tenant_id: str,
) -> None:
    """
    Send a reply message to Slack (from Intelligence Service).
    
    Args:
        reply: Reply payload from Intelligence Service
        tenant_id: Tenant ID
    """
    slack_client = get_slack_client()
    
    logger.info(
        "sending_slack_reply",
        channel=reply.slack_channel_id,
        thread_ts=reply.slack_thread_ts,
        tenant_id=tenant_id,
    )
    
    # Post reply to Slack
    await slack_client.post_message(
        channel=reply.slack_channel_id,
        text=reply.message_text,
        blocks=reply.blocks,
        thread_ts=reply.slack_thread_ts,
        tenant_id=tenant_id,
    )
    
    logger.info(
        "slack_reply_sent",
        channel=reply.slack_channel_id,
        thread_ts=reply.slack_thread_ts,
        tenant_id=tenant_id,
    )
