from typing import Optional
from fastapi import Request
from src.middleware.tenant.base import TenantExtractor

class HeaderTenantExtractor(TenantExtractor):
    async def extract(self, request: Request) -> Optional[str]:
        return request.headers.get("X-Tenant-ID")
