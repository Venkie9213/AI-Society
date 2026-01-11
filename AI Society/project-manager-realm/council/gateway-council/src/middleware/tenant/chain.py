from typing import List, Optional
from fastapi import Request
from src.middleware.tenant.base import TenantExtractor
from src.middleware.tenant.header import HeaderTenantExtractor
from src.middleware.tenant.slack import SlackTenantExtractor

class TenantExtractorChain:
    def __init__(self, extractors: List[TenantExtractor]):
        self.extractors = extractors

    async def extract(self, request: Request) -> Optional[str]:
        for extractor in self.extractors:
            tenant_id = await extractor.extract(request)
            if tenant_id:
                return tenant_id
        return None

default_chain = TenantExtractorChain([
    HeaderTenantExtractor(),
    SlackTenantExtractor()
])
