import hmac
import hashlib
import time
from fastapi import Request, HTTPException, status
from src.middleware.signature.base import SignatureVerifier
from src.config.settings import settings

class SlackSignatureVerifier(SignatureVerifier):
    async def verify(self, request: Request) -> None:
        slack_signature = request.headers.get("X-Slack-Signature")
        slack_timestamp = request.headers.get("X-Slack-Request-Timestamp")

        if not slack_signature or not slack_timestamp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Slack signature headers",
            )

        if abs(int(time.time()) - int(slack_timestamp)) > 300:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Request timestamp too old",
            )

        body = await request.body()
        request.state.body = body

        sig_basestring = b"v0:" + slack_timestamp.encode("utf-8") + b":" + body
        expected_hmac = hmac.new(
            settings.project_manager_slack_signing_secret.encode("utf-8"),
            sig_basestring,
            hashlib.sha256,
        ).hexdigest()
        expected_signature = "v0=" + expected_hmac

        if not hmac.compare_digest(expected_signature, slack_signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid request signature",
            )
