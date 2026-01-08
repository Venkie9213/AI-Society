# app/providers/base.py
"""Base interface for LLM providers"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class LLMMessage:
    """Represents a message in a conversation"""
    role: str  # user, assistant, system
    content: str


@dataclass
class LLMResponse:
    """Response from LLM provider"""
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    stop_reason: str = "stop"
    cost_cents: float = 0.0


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize provider with configuration"""
        self.config = config
        self.provider_name = self.__class__.__name__
    
    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from LLM
        
        Args:
            messages: List of messages in conversation
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Provider-specific parameters
            
        Returns:
            LLMResponse object with generated content
        """
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings for text
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider connectivity
        
        Returns:
            True if provider is accessible, False otherwise
        """
        pass
    
    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for API call in USD cents
        
        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            
        Returns:
            Cost in USD cents
        """
        # Override in subclass with provider-specific pricing
        return 0.0
    
    def __repr__(self) -> str:
        return f"{self.provider_name}(model={self.config.get('model', 'unknown')})"
