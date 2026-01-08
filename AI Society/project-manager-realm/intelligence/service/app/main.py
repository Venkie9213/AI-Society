# app/main.py
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn

from app.config import get_settings
from app.database import init_db, get_db_pool, close_db_pool
from app.observability.logging import setup_logging
from app.observability.metrics import setup_metrics
from app.providers.manager import init_provider_router
from app.loaders import get_config_loader
from app.orchestration import get_agent_orchestrator
from app.api import health, debug, providers, agents

# Setup structured logging
settings = get_settings()
setup_logging(settings.log_level, settings.structured_logs)
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """FastAPI lifespan manager for startup/shutdown events"""
    
    settings = get_settings()
    
    # Startup
    logger.info("app_startup", version=settings.app_version)
    
    # Initialize database
    try:
        await init_db(settings.database_url)
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        raise
    
    # Initialize metrics
    try:
        setup_metrics()
        logger.info("metrics_initialized")
    except Exception as e:
        logger.error("metrics_initialization_failed", error=str(e))
    
    # Initialize provider router
    try:
        init_provider_router()
        logger.info("provider_router_initialized")
    except Exception as e:
        logger.error("provider_router_initialization_failed", error=str(e))
        # Don't raise - continue with app even if providers fail
    
    # Load all intelligence configurations (providers, agents, prompts)
    try:
        config_loader = get_config_loader()
        await config_loader.load_all_configs()
        logger.info("intelligence_configs_loaded")
    except Exception as e:
        logger.error("intelligence_configs_load_failed", error=str(e))
        # Don't raise - continue with app even if configs fail
    
    # Initialize agent orchestrator
    try:
        orchestrator = get_agent_orchestrator()
        logger.info("agent_orchestrator_initialized")
    except Exception as e:
        logger.error("agent_orchestrator_initialization_failed", error=str(e))
        # Don't raise - continue with app even if orchestrator fails
    
    # TODO: Initialize Kafka consumer/producer
    # TODO: Initialize vector store
    # TODO: Initialize LLM providers
    
    yield
    
    # Shutdown
    logger.info("app_shutdown")
    
    # Close database connections
    try:
        await close_db_pool()
        logger.info("database_closed")
    except Exception as e:
        logger.error("database_close_failed", error=str(e))


# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Society Intelligence Service - LLM-powered conversational reasoning",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_type=type(exc).__name__,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if config.debug else "An error occurred",
        },
    )


# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(debug.router, prefix="/api/v1/debug", tags=["debug"])
app.include_router(providers.router, prefix="/api/v1", tags=["providers"])
app.include_router(agents.router, prefix="/api/v1", tags=["agents"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    settings = get_settings()
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
    }


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
