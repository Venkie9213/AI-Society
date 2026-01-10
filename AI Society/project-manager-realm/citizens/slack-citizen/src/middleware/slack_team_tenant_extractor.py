import json
from typing import Optional
from src.utils.observability import get_logger
from src.middleware.tenant_extractor import TenantExtractor

logger = get_logger(__name__)

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
