"""LLM Safety settings and content policy configuration.

Centralizes safety and content filtering policies for LLM providers.
"""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

try:
    from google import genai
except ImportError:
    genai = None


class SafetyPolicy(ABC):
    """Abstract safety policy interface."""
    
    @abstractmethod
    def get_settings(self) -> Any:
        """Get safety settings for provider."""
        pass


class GeminiSafetyPolicy(SafetyPolicy):
    """Gemini-specific safety policy."""
    
    def __init__(self, block_none: bool = True):
        """Initialize Gemini safety policy.
        
        Args:
            block_none: If True, allow all content (development mode)
        """
        self.block_none = block_none
    
    def get_settings(self) -> Optional[List[Any]]:
        """Get Gemini safety settings.
        
        Returns:
            List of SafetySetting objects or None if genai not available
        """
        if genai is None:
            return None
        
        if not self.block_none:
            return []
        
        # Allow all content for development
        try:
            return [
                genai.types.SafetySetting(
                    category=genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=genai.types.HarmBlockThreshold.BLOCK_NONE,
                ),
                genai.types.SafetySetting(
                    category=genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=genai.types.HarmBlockThreshold.BLOCK_NONE,
                ),
                genai.types.SafetySetting(
                    category=genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=genai.types.HarmBlockThreshold.BLOCK_NONE,
                ),
                genai.types.SafetySetting(
                    category=genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=genai.types.HarmBlockThreshold.BLOCK_NONE,
                ),
            ]
        except (AttributeError, TypeError):
            # Fallback for different google-genai versions
            return []


class SafetyPolicyFactory:
    """Factory for creating safety policies."""
    
    @staticmethod
    def create_gemini_policy(block_none: bool = True) -> GeminiSafetyPolicy:
        """Create Gemini safety policy.
        
        Args:
            block_none: If True, allow all content
            
        Returns:
            GeminiSafetyPolicy instance
        """
        return GeminiSafetyPolicy(block_none=block_none)
