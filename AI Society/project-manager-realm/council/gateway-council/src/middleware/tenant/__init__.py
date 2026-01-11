from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
from src.middleware.tenant.chain import default_chain

class TenantResolutionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        tenant_id = await default_chain.extract(request)
        request.state.tenant_id = tenant_id or "default"
        
        return await call_next(request)
