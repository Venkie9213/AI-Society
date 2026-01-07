"""Health check endpoints."""

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from src.config import settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    service: str
    version: str
    timestamp: datetime


class ReadinessResponse(BaseModel):
    """Readiness check response model."""

    ready: bool
    service: str
    checks: dict[str, bool]


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns service health status.
    """
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.utcnow(),
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness check endpoint.
    
    Returns whether the service is ready to accept requests.
    """
    # TODO: Add actual health checks for Kafka, Slack API, etc.
    checks = {
        "kafka": True,  # Check Kafka connection
        "slack_api": True,  # Check Slack API availability
    }

    return ReadinessResponse(
        ready=all(checks.values()),
        service=settings.app_name,
        checks=checks,
    )


@router.get("/metrics")
async def metrics() -> dict[str, str]:
    """
    Prometheus metrics endpoint.
    
    Note: Actual metrics are served by prometheus_client on a separate port.
    This endpoint just provides information about the metrics endpoint.
    """
    return {
        "metrics_url": f"http://localhost:{settings.prometheus_port}/metrics",
        "note": "Prometheus metrics are available on the configured port",
    }
