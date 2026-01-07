"""Multi-tenancy middleware for tenant isolation."""

from typing import Callable, Optional

import httpx
from fastapi import HTTPException, Request, Response, status

from src.config import settings
from src.utils.observability import add_context, clear_context, get_logger

logger = get_logger(__name__)


class TenantMiddleware:
    """Middleware to extract and validate tenant IDs."""

    def __init__(self, app: Callable) -> None:
        """Initialize the middleware."""
        self.app = app
        self._tenant_cache: dict[str, str] = {}  # slack_team_id -> tenant_id

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Extract tenant ID from request."""
        # Skip tenant extraction for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        # Extract tenant ID based on request type
        tenant_id: Optional[str] = None
        
        if request.url.path.startswith("/webhooks/slack"):
            # Extract from Slack team_id in body
            body = getattr(request.state, "body", None)
            if body:
                import json
                try:
                    data = json.loads(body)
                    slack_team_id = data.get("team_id")
                    if slack_team_id:
                        tenant_id = await self._map_slack_team_to_tenant(slack_team_id)
                except Exception as e:
                    logger.error(
                        "failed_to_extract_tenant_from_body",
                        error=str(e),
                    )
        else:
            # Extract from header for internal requests
            tenant_id = request.headers.get("X-Tenant-ID")

        # Use default tenant if mapping fails
        if not tenant_id:
            tenant_id = settings.default_tenant_id
            logger.warning(
                "using_default_tenant",
                path=request.url.path,
                default_tenant_id=tenant_id,
            )

        # Store in request state
        request.state.tenant_id = tenant_id

        # Add to logging context
        add_context(tenant_id=tenant_id)

        try:
            # Process request
            response = await call_next(request)
            return response

        finally:
            # Clean up logging context
            clear_context("tenant_id")

    async def _map_slack_team_to_tenant(self, slack_team_id: str) -> str:
        """
        Map Slack team ID to internal tenant ID.
        
        Args:
            slack_team_id: Slack workspace/team ID
        
        Returns:
            Internal tenant ID
        """
        # Check cache first
        if slack_team_id in self._tenant_cache:
            return self._tenant_cache[slack_team_id]

        # TODO: Call tenant mapping service
        # For now, use simple 1:1 mapping
        tenant_id = f"tenant_{slack_team_id}"
        
        # Optionally call mapping service
        if settings.tenant_mapping_service_url != "http://localhost:8080/api/tenants":
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(
                        f"{settings.tenant_mapping_service_url}/by-slack-team/{slack_team_id}"
                    )
                    if response.status_code == 200:
                        data = response.json()
                        tenant_id = data.get("tenant_id", tenant_id)
            except Exception as e:
                logger.warning(
                    "tenant_mapping_service_unavailable",
                    slack_team_id=slack_team_id,
                    error=str(e),
                )

        # Cache the mapping
        self._tenant_cache[slack_team_id] = tenant_id
        
        logger.debug(
            "tenant_mapped",
            slack_team_id=slack_team_id,
            tenant_id=tenant_id,
        )

        return tenant_id


def get_tenant_id(request: Request) -> str:
    """
    Get tenant ID from request state.
    
    Args:
        request: FastAPI request object
    
    Returns:
        Tenant ID
    """
    return getattr(request.state, "tenant_id", settings.default_tenant_id)
