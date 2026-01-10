from abc import ABC, abstractmethod
from typing import Optional

class TenantExtractor(ABC):
    """Abstract base for tenant ID extraction strategies."""

    @abstractmethod
    async def extract(self, **kwargs) -> Optional[str]:
        """Extract tenant ID from request context."""
        pass
