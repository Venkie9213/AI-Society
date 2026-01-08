# app/api/debug.py
"""Debug endpoints for development"""

from fastapi import APIRouter
from app.config import config
import structlog

logger = structlog.get_logger()

router = APIRouter()


@router.get("/config")
async def get_config():
    """Get current configuration (debug only)"""
    if not config.debug:
        return {"error": "Not available in production"}
    
    return {
        "app_name": config.app_name,
        "app_version": config.app_version,
        "debug": config.debug,
        "environment": config.environment,
        "llm": {
            "primary_provider": config.llm.primary_provider,
            "gemini_model": config.llm.gemini_model,
        },
        "database": {
            "database_url": config.database.database_url.split("@")[0] + "@***",  # Mask password
        },
        "vector_store": {
            "provider": config.vector_store.provider,
        },
    }


@router.get("/info")
async def info():
    """Service information"""
    return {
        "service": config.app_name,
        "version": config.app_version,
        "environment": config.environment,
        "debug_mode": config.debug,
    }
