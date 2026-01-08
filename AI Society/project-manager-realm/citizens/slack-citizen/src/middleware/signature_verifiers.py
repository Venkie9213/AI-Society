"""Request signature verification strategies (Strategy Pattern)."""

import hashlib
import hmac
import time
from abc import ABC, abstractmethod

from fastapi import HTTPException, status

from src.config import settings
from src.utils.observability import get_logger

logger = get_logger(__name__)


class SignatureVerifier(ABC):
    """Abstract base for signature verification strategies."""

    @abstractmethod
    async def verify(self, request) -> None:
        """Verify request signature."""
        pass


class SlackSignatureVerifier(SignatureVerifier):
    """Verifies Slack request signatures using HMAC-SHA256."""

    async def verify(self, request) -> None:
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

        # Compute expected signature using exact raw bytes
        try:
            sig_basestring = b"v0:" + slack_timestamp.encode("utf-8") + b":" + body
            expected_hmac = hmac.new(
                settings.project_manager_slack_signing_secret.encode("utf-8"),
                sig_basestring,
                hashlib.sha256,
            ).hexdigest()
            expected_signature = "v0=" + expected_hmac
        except Exception as exc:
            logger.exception("failed_to_compute_expected_signature", exc=exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to compute signature",
            )

        # Compare signatures
        if not hmac.compare_digest(expected_signature, slack_signature):
            logger.warning(
                "slack_signature_mismatch",
                expected=expected_signature[:10],
                received=slack_signature[:10],
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid request signature",
            )

        logger.debug("slack_signature_verified")
