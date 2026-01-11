import httpx
from src.utils.observability import get_logger
from src.config.settings import settings

logger = get_logger("discovery_client")

class DiscoveryClient:
    """Client for self-registration with the gateway's service registry."""
    
    def __init__(self, service_name: str):
        self.gateway_url = getattr(settings, "gateway_url", "http://gateway-council:8000")
        self.service_name = service_name
        self.service_url = getattr(settings, "service_url", f"http://{service_name}:8000")
        logger.info("discovery_client_initialized", gateway_url=self.gateway_url)

    async def register(self):
        """Register the service with the gateway."""
        registration_data = {
            "name": self.service_name,
            "url": self.service_url,
            "metadata": {
                "version": settings.app_version,
                "type": "council-service"
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
