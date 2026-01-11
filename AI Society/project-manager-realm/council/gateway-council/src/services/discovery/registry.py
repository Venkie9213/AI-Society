import json
import redis
import structlog
from datetime import datetime
from typing import Optional, Dict, List, Any
from src.config.settings import settings

logger = structlog.get_logger(__name__)

class ServiceRegistry:
    """Redis-backed registry for dynamic service discovery."""
    
    REDIS_PREFIX = "gateway:discovery:services"
    
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True
        )
        logger.info("service_registry_connected", host=settings.redis_host, port=settings.redis_port)

    def register_service(self, name: str, url: str, metadata: Optional[Dict[str, Any]] = None):
        """Register or update a service in the registry."""
        data = {
            "name": name,
            "url": url,
            "metadata": json.dumps(metadata or {}),
            "updated_at": datetime.utcnow().isoformat()
        }
        self.redis.hset(self.REDIS_PREFIX, name, json.dumps(data))
        logger.info("service_registered", service=name, url=url)

    def get_service(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve service details from the registry."""
        raw_data = self.redis.hget(self.REDIS_PREFIX, name)
        if not raw_data:
            return None
        
        data = json.loads(raw_data)
        data["metadata"] = json.loads(data["metadata"])
        return data

    def list_services(self) -> List[Dict[str, Any]]:
        """List all registered services."""
        all_services = self.redis.hgetall(self.REDIS_PREFIX)
        services_list = []
        for name, raw_data in all_services.items():
            data = json.loads(raw_data)
            data["metadata"] = json.loads(data["metadata"])
            services_list.append(data)
        return services_list

    def unregister_service(self, name: str):
        """Remove a service from the registry."""
        self.redis.hdel(self.REDIS_PREFIX, name)
        logger.info("service_unregistered", service=name)

# Global registry instance
registry = ServiceRegistry()
