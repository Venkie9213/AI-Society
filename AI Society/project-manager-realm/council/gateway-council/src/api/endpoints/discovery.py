from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from src.services.discovery.registry import registry

router = APIRouter(prefix="/discovery", tags=["discovery"])

class ServiceRegistration(BaseModel):
    name: str
    url: str
    metadata: Optional[Dict[str, Any]] = None

@router.post("/register")
async def register(service: ServiceRegistration):
    """Endpoint for services to self-register."""
    registry.register_service(service.name, service.url, service.metadata)
    return {"status": "registered", "service": service.name}

@router.get("/catalog")
async def catalog() -> List[Dict[str, Any]]:
    """List all registered services."""
    return registry.list_services()

@router.delete("/unregister/{name}")
async def unregister(name: str):
    """Endpoint to manually unregister a service."""
    registry.unregister_service(name)
    return {"status": "unregistered", "service": name}
