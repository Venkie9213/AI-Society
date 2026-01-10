from abc import ABC, abstractmethod

class SignatureVerifier(ABC):
    """Abstract base for signature verification strategies."""

    @abstractmethod
    async def verify(self, request) -> None:
        """Verify request signature."""
        pass
