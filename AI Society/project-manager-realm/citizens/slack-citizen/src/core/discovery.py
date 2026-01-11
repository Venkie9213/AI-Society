import httpx
import structlog
from typing import Optional, Dict, Any
from src.config import settings

logger = structlog.get_logger(__name__)

class DiscoveryClient:
    """Client for self-registration with the gateway's service registry."""
    
    def __init__(self):
        self.gateway_url = settings.gateway_url
        self.service_name = "slack-citizen"
        self.service_url = settings.service_url
        logger.info("discovery_client_initialized", gateway_url=self.gateway_url)

    async def register(self):
        """Register the service with the gateway."""
        registration_data = {
            "name": self.service_name,
            "url": self.service_url,
            "metadata": {
                "version": settings.app_version,
                "type": "citizen"
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.gateway_url}/discovery/register",
                    json=registration_data,
                    timeout=5.0
                )
                response.raise_for_status()
                logger.info("service_registration_successful", service=self.service_name)
        except Exception as e:
            logger.error("service_registration_failed", error=str(e))

    async def unregister(self):
        """Unregister the service from the gateway."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.gateway_url}/discovery/unregister/{self.service_name}",
                    timeout=5.0
                )
                response.raise_for_status()
                logger.info("service_unregistration_successful", service=self.service_name)
        except Exception as e:
            logger.error("service_unregistration_failed", error=str(e))
