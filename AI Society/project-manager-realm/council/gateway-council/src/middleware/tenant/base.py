from abc import ABC, abstractmethod
from typing import Optional
from fastapi import Request

class TenantExtractor(ABC):
    @abstractmethod
    async def extract(self, request: Request) -> Optional[str]:
        pass
