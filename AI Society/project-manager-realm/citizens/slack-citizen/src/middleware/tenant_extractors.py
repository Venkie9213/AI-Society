"""Tenant extraction strategies for multi-tenancy support (Strategy Pattern)."""

import json
from abc import ABC, abstractmethod
from typing import Optional

from src.utils.observability import get_logger

logger = get_logger(__name__)


class TenantExtractor(ABC):
    """Abstract base for tenant ID extraction strategies."""

    @abstractmethod
    async def extract(self, **kwargs) -> Optional[str]:
        """Extract tenant ID from request context."""
        pass


class SlackTeamTenantExtractor(TenantExtractor):
    """Extracts tenant ID from Slack team_id in request body."""

    async def extract(self, body: bytes) -> Optional[str]:
        """Extract tenant ID from Slack event body."""
        if not body:
            return None

        try:
            data = json.loads(body)
            slack_team_id = data.get("team_id")
            logger.debug(
                "extracted_slack_team_id",
                slack_team_id=slack_team_id,
            )
            return slack_team_id
        except Exception as e:
            logger.error(
                "failed_to_extract_slack_team_id",
                error=str(e),
            )
            return None


class HeaderTenantExtractor(TenantExtractor):
    """Extracts tenant ID from X-Tenant-ID header."""

    async def extract(self, headers: dict) -> Optional[str]:
        """Extract tenant ID from request headers."""
        tenant_id = headers.get("X-Tenant-ID")
        if tenant_id:
            logger.debug("extracted_tenant_from_header", tenant_id=tenant_id)
        return tenant_id


class TenantExtractorChain:
    """Chains multiple tenant extractors (Chain of Responsibility)."""

    def __init__(self, extractors: list[TenantExtractor]):
        """Initialize with a list of extractors."""
        self.extractors = extractors

    async def extract(self, **kwargs) -> Optional[str]:
        """Try extractors in order until one succeeds."""
        for extractor in self.extractors:
            try:
                tenant_id = await extractor.extract(**kwargs)
                if tenant_id:
                    return tenant_id
            except Exception as e:
                logger.debug(
                    "tenant_extractor_failed",
                    extractor=extractor.__class__.__name__,
                    error=str(e),
                )
                continue
        return None
