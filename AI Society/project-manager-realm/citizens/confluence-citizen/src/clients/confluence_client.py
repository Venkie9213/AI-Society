import httpx
import base64
import structlog
from typing import Dict, Any, Optional
from src.schemas.confluence_schemas import ConfluenceConfig

logger = structlog.get_logger(__name__)

class ConfluenceClient:
    """Client for interacting with Confluence Cloud REST API."""
    
    def __init__(self, config: ConfluenceConfig):
        self.config = config
        self.base_url = config.url.rstrip("/")
        self.api_url = f"{self.base_url}/wiki/rest/api"
        
        # Prepare Auth Header
        auth_str = f"{config.username}:{config.api_token}"
        auth_bytes = auth_str.encode("utf-8")
        auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
        
        self.headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
    async def create_page(
        self, 
        title: str, 
        content_xhtml: str, 
        space_key: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new page in Confluence."""
        url = f"{self.api_url}/content"
        
        space = space_key or self.config.space_key
        
        payload = {
            "type": "page",
            "title": title,
            "space": {"key": space},
            "body": {
                "storage": {
                    "value": content_xhtml,
                    "representation": "storage"
                }
            }
        }
        
        if parent_id:
            payload["ancestors"] = [{"id": parent_id}]
            
        async with httpx.AsyncClient() as client:
            logger.info("creating_confluence_page", title=title, space=space)
            response = await client.post(url, json=payload, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(
                    "confluence_page_creation_failed", 
                    status_code=response.status_code, 
                    response=response.text
                )
                response.raise_for_status()
                
            result = response.json()
            logger.info("confluence_page_created", page_id=result.get("id"), url=result.get("_links", {}).get("base") + result.get("_links", {}).get("webui"))
            return result

    async def get_space(self, space_key: str) -> Dict[str, Any]:
        """Get information about a Confluence space."""
        url = f"{self.api_url}/space/{space_key}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
