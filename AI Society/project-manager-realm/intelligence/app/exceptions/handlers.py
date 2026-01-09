"""Exception handlers for FastAPI."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import structlog

from app.exceptions.exceptions import AppException

logger = structlog.get_logger()


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers with FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """Handle application exceptions."""
        logger.error(
            "app_exception",
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            path=request.url.path,
            details=exc.details,
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "code": exc.code,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": exc.details,
            },
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.error(
            "unexpected_exception",
            type=type(exc).__name__,
            message=str(exc),
            path=request.url.path,
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "code": "INTERNAL_ERROR",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
