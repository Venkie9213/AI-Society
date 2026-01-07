"""Slack signature verification middleware."""

from typing import Callable

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse

from src.middleware.signature_verifiers import SlackSignatureVerifier
from src.utils.observability import get_logger

logger = get_logger(__name__)


class SlackSignatureMiddleware:
    """Middleware to verify Slack request signatures using strategy pattern."""

    def __init__(self, app: Callable) -> None:
        """Initialize the middleware."""
        self.app = app
        self.verifier = SlackSignatureVerifier()

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Verify Slack signature for webhook requests."""
        # Only verify for Slack webhook endpoints
        if not request.url.path.startswith("/webhooks/slack"):
            return await call_next(request)

        try:
            await self.verifier.verify(request)
        except HTTPException as e:
            logger.warning(
                "slack_signature_verification_failed",
                path=request.url.path,
                status_code=e.status_code,
                detail=e.detail,
            )
            return JSONResponse(
                status_code=e.status_code,
                content={"error": e.detail},
            )

        return await call_next(request)
