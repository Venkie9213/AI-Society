# app/api/health.py
"""Health check endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.database import get_session
from app.observability.metrics import get_metrics

logger = structlog.get_logger()

router = APIRouter()


@router.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)):
    """Health check endpoint that verifies database connectivity"""
    try:
        # Test database connection
        result = await session.execute(text("SELECT 1"))
        db_status = "healthy" if result else "unhealthy"
        
        return {
            "status": "operational" if db_status == "healthy" else "degraded",
            "database": db_status,
            "service": "intelligence-service",
        }
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        return {
            "status": "unhealthy",
            "database": "unhealthy",
            "service": "intelligence-service",
            "error": str(e),
        }


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return get_metrics()


@router.get("/ready")
async def readiness_probe(session: AsyncSession = Depends(get_session)):
    """Readiness probe for Kubernetes/orchestration"""
    try:
        await session.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception as e:
        logger.error("readiness_probe_failed", error=str(e))
        return {"ready": False, "error": str(e)}


@router.get("/live")
async def liveness_probe():
    """Liveness probe for Kubernetes/orchestration"""
    return {"live": True}
