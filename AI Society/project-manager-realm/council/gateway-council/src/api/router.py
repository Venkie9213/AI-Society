from fastapi import APIRouter, Request, HTTPException
from src.config.settings import settings
from src.services.proxy.service import ProxyService
from src.services.discovery.registry import registry

proxy_router = APIRouter()

@proxy_router.api_route("/webhooks/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def dynamic_proxy(request: Request, service_name: str, path: str):
    """Dynamically route requests based on service registration."""
    # Mapping path prefix to service naming convention if necessary
    # For now, let's assume service_name in URL matches registry name (e.g., slack-citizen)
    # But wait, the original routes were /webhooks/slack/ and /webhooks/confluence/
    
    registry_name = f"{service_name}-citizen"
    service = registry.get_service(registry_name)
    
    if not service:
        # Fallback to hardcoded settings for migration period or special cases
        if service_name == "slack":
            target_url = f"{settings.slack_citizen_url}/webhooks/slack/{path}"
        elif service_name == "confluence":
            target_url = f"{settings.confluence_citizen_url}/webhooks/confluence/{path}"
        else:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found in registry")
    else:
        target_url = f"{service['url']}/webhooks/{service_name}/{path}"
    
    return await ProxyService.forward_request(request, target_url)
