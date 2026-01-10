from typing import Optional
from src.utils.observability import get_logger
from src.middleware.tenant_extractor import TenantExtractor

logger = get_logger(__name__)

class HeaderTenantExtractor(TenantExtractor):
    """Extracts tenant ID from X-Tenant-ID header."""

    async def extract(self, headers: dict) -> Optional[str]:
        """Extract tenant ID from request headers."""
        tenant_id = headers.get("X-Tenant-ID")
        if tenant_id:
            logger.debug("extracted_tenant_from_header", tenant_id=tenant_id)
        return tenant_id
