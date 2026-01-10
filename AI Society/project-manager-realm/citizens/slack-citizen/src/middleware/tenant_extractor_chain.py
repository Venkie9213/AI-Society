from typing import Optional
from src.utils.observability import get_logger
from src.middleware.tenant_extractor import TenantExtractor

logger = get_logger(__name__)

class TenantExtractorChain:
    """Chains multiple tenant extractors (Chain of Responsibility)."""

    def __init__(self, extractors: list[TenantExtractor]):
        """Initialize with a list of extractors."""
        self.extractors = extractors

    async def extract(self, **kwargs) -> Optional[str]:
        """Try extractors in order until one succeeds."""
        for extractor in self.extractors:
            try:
                tenant_id = await extractor.extract(**kwargs)
                if tenant_id:
                    return tenant_id
            except Exception as e:
                logger.debug(
                    "tenant_extractor_failed",
                    extractor=extractor.__class__.__name__,
                    error=str(e),
                )
                continue
        return None
