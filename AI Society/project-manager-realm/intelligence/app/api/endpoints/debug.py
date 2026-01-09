# app/api/debug.py
"""Debug endpoints for development"""

from fastapi import APIRouter
from app.config import get_settings
import structlog

logger = structlog.get_logger()

router = APIRouter()


@router.get("/config")
async def get_config():
    """Get current configuration (debug only)"""
    settings = get_settings()
    if not settings.debug:
        return {"error": "Not available in production"}
    
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "debug": settings.debug,
        "environment": settings.environment,
        "llm": {
            "default_provider": settings.default_provider,
            "gemini_model": settings.gemini_model,
        },
        "database": {
            "database_url": settings.database_url.split("@")[0] + "@***",  # Mask password
        },
        "vector_store": {
            "provider": settings.vector_store_provider,
        },
    }


@router.get("/info")
async def info():
    """Service information"""
    settings = get_settings()
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "debug_mode": settings.debug,
    }
