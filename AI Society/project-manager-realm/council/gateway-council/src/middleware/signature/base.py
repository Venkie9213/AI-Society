from abc import ABC, abstractmethod
from fastapi import Request

class SignatureVerifier(ABC):
    @abstractmethod
    async def verify(self, request: Request) -> None:
        pass
