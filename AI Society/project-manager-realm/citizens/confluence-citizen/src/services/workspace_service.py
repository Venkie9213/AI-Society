import structlog
from typing import Optional
from src.schemas.confluence_schemas import ConfluenceConfig
from src.config.settings import settings

logger = structlog.get_logger(__name__)

import httpx

class WorkspaceService:
    """Service to fetch workspace-specific configurations from Workspace Council."""
    
    def __init__(self):
        self.base_url = settings.workspace_council_url

    async def get_confluence_config(self, tenant_id: str) -> Optional[ConfluenceConfig]:
        """Fetch Confluence configuration for a specific tenant via Workspace Council API.
        
        Args:
            tenant_id: The unique identifier for the workspace/tenant
            
        Returns:
            ConfluenceConfig if found, None otherwise
        """
        logger.info("fetching_confluence_config", tenant_id=tenant_id, service="workspace-council")
        
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/api/v1/workspaces/{tenant_id}/confluence/config"
                response = await client.get(url, timeout=5.0)
                
                if response.status_code == 200:
                    data = response.json()
                    config_data = data.get("config", {})
                    config = ConfluenceConfig(
                        url=config_data.get("url"),
                        username=config_data.get("username"),
                        api_token=config_data.get("api_token"),
                        space_key=config_data.get("space_key", "~")
                    )
                    logger.info("workspace_config_resolved_via_rpc", tenant_id=tenant_id)
                    return config
                else:
                    logger.warning("workspace_council_lookup_failed", status=response.status_code, tenant_id=tenant_id)

        except Exception as e:
            logger.error("workspace_council_connection_failed", error=str(e), tenant_id=tenant_id)

        # Fallback to local settings for demonstration/development
        if settings.confluence_api_token:
            logger.info("using_fallback_local_settings", tenant_id=tenant_id)
            return ConfluenceConfig(
                url=settings.confluence_url,
                username=settings.confluence_username,
                api_token=settings.confluence_api_token,
                space_key=settings.confluence_default_space
            )
            
        return None
