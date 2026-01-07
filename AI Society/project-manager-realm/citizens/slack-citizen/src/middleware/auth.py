"""Slack signature verification middleware."""

import hashlib
import hmac
import time
from typing import Callable

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from src.config import settings
from src.utils.observability import get_logger

logger = get_logger(__name__)


class SlackSignatureMiddleware:
    """Middleware to verify Slack request signatures."""

    def __init__(self, app: Callable) -> None:
        """Initialize the middleware."""
        self.app = app

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Verify Slack signature for webhook requests."""
        # Only verify for Slack webhook endpoints
        if not request.url.path.startswith("/webhooks/slack"):
            return await call_next(request)

        try:
            await self._verify_slack_signature(request)
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

    async def _verify_slack_signature(self, request: Request) -> None:
        """
        Verify Slack request signature.
        
        Args:
            request: FastAPI request object
        
        Raises:
            HTTPException: If signature verification fails
        """
        # Get signature from headers
        slack_signature = request.headers.get("X-Slack-Signature")
        slack_timestamp = request.headers.get("X-Slack-Request-Timestamp")

        if not slack_signature or not slack_timestamp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Slack signature headers",
            )

        # Check timestamp to prevent replay attacks (within 5 minutes)
        current_timestamp = int(time.time())
        if abs(current_timestamp - int(slack_timestamp)) > 300:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Request timestamp too old",
            )

        # Read raw request body (bytes)
        body = await request.body()

        # Store body for later use (since we consumed it)
        request.state.body = body

        # Compute expected signature using exact raw bytes to avoid encoding differences
        try:
            sig_basestring = b"v0:" + slack_timestamp.encode("utf-8") + b":" + body
            expected_hmac = hmac.new(
                settings.slack_signing_secret.encode("utf-8"),
                sig_basestring,
                hashlib.sha256,
            ).hexdigest()
            expected_signature = "v0=" + expected_hmac
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("failed_to_compute_expected_signature", exc=exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to compute signature",
            )

        # Compare signatures and log helpful debug info on mismatch
        if not hmac.compare_digest(expected_signature, slack_signature):
            # Log header + preview of body for debugging (avoid logging secrets)
            body_preview = None
            try:
                body_preview = body.decode("utf-8", errors="replace")[:1024]
            except Exception:
                body_preview = f"<non-decodable-bytes length={len(body)}>"

            logger.warning(
                "slack_signature_mismatch",
                path=request.url.path,
                received_signature=slack_signature,
                expected_signature=expected_signature,
                timestamp=slack_timestamp,
                body_length=len(body),
                body_preview=body_preview,
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Slack signature",
            )

        logger.debug(
            "slack_signature_verified",
            path=request.url.path,
            timestamp=slack_timestamp,
        )
