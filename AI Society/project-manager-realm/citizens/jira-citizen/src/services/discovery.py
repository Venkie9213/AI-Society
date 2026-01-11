import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from src.config.settings import settings
from src.utils.observability import get_logger
from typing import Optional, Dict, Any

logger = get_logger(__name__)

class DiscoveryService:
    """Service to resolve other service URLs using the Gateway's service catalog."""
    
    _cache: Dict[str, str] = {}
    
    @classmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_service_url(cls, service_name: str) -> Optional[str]:
        """
        Get the base URL for a service.
        Checks cache first, then queries the Gateway.
        """
        if service_name in cls._cache:
            return cls._cache[service_name]
            
        try:
            async with httpx.AsyncClient() as client:
                # Gateway's catalog endpoint usually returns a list or we might need a specific lookup endpoint
                # Provided plan assumption: Gateway has a way to look up services. 
                # Based on `gateway-council` code seen earlier, it has `/discovery/catalog`.
                # We can also implement a direct lookup if supported, but for now we'll fetch catalog and filter.
                
                # Ideally, we should add a specific lookup endpoint to gateway, but to minimize scope creep
                # we will fetch the catalog. If catalog is huge, this is inefficient, but acceptable for now.
                response = await client.get(f"{settings.gateway_url}/discovery/catalog")
                response.raise_for_status()
                services = response.json()
                
                for service in services:
                    if service["name"] == service_name:
                        url = service["url"]
                        cls._cache[service_name] = url
                        logger.info("service_url_resolved", service=service_name, url=url)
                        return url
                        
            logger.warning("service_not_found_in_discovery", service=service_name)
            return None
            
        except Exception as e:
            logger.error("discovery_lookup_failed", service=service_name, error=str(e))
            raise

    @classmethod
    def clear_cache(cls):
        cls._cache = {}
