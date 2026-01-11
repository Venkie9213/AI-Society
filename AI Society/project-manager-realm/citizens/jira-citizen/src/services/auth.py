import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from src.services.discovery import DiscoveryService
from src.utils.observability import get_logger
from typing import Optional, Dict

logger = get_logger(__name__)

class AuthService:
    """Service to fetch authentication credentials from Workspace Council."""
    
    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_jira_credentials(tenant_id: str) -> Optional[Dict[str, str]]:
        """
        Fetch JIRA credentials for a given tenant.
        """
        workspace_council_url = await DiscoveryService.get_service_url("workspace-council")
        if not workspace_council_url:
            raise RuntimeError("Could not resolve workspace-council URL")
            
        try:
            async with httpx.AsyncClient() as client:
                # Assuming workspace-council has an endpoint: GET /api/v1/workspaces/{tenant_id}/jira/config
                # Based on existing code: `/api/v1/workspaces/{tenant_id}/{type}/config`
                url = f"{workspace_council_url}/api/v1/workspaces/{tenant_id}/jira/config"
                response = await client.get(url)
                
                if response.status_code == 404:
                    logger.warning("jira_config_not_found", tenant_id=tenant_id)
                    return None
                    
                response.raise_for_status()
                data = response.json()
                return data.get("config") # Wrapper is { ..., config: {...} }
                
        except Exception as e:
            logger.error("credential_fetch_failed", tenant_id=tenant_id, error=str(e))
            raise
