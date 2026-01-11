import httpx
from fastapi import Request, Response

class ProxyService:
    @staticmethod
    async def forward_request(request: Request, target_url: str) -> Response:
        async with httpx.AsyncClient() as client:
            headers = dict(request.headers)
            
            # Inject resolved tenant ID
            if hasattr(request.state, "tenant_id"):
                headers["X-Tenant-ID"] = request.state.tenant_id
            
            # Use cached body if available
            content = getattr(request.state, "body", await request.body())
            
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=content,
                params=dict(request.query_params)
            )
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
