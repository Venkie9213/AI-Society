# app/api/health.py
"""Health check endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.config import database as db_module
from app.observability.metrics import get_metrics

logger = structlog.get_logger()

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint that verifies database connectivity"""
    # Check if database is initialized by checking the module-level variable
    if db_module._async_session_factory is None:
        return {
            "status": "degraded",
            "database": "not_initialized",
            "service": "intelligence-service",
            "note": "Database not initialized - running in test mode",
        }
    
    try:
        # Test database connection
        async with db_module._async_session_factory() as session:
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
async def readiness_probe():
    """Readiness probe for Kubernetes/orchestration"""
    try:
        # Use the module-level factory directly to avoid circular imports
        if db_module._async_session_factory is None:
            return {"ready": False, "error": "Database not initialized"}
        
        async with db_module._async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            return {"ready": True}
    except Exception as e:
        logger.error("readiness_probe_failed", error=str(e))
        return {"ready": False, "error": str(e)}


@router.get("/live")
async def liveness_probe():
    """Liveness probe for Kubernetes/orchestration"""
    return {"live": True}
