# app/providers/gemini.py
"""Google Gemini LLM Provider Implementation

Uses the new unified google.genai.Client syntax (v1.0+)
Compatible with Gemini 3, 2.5, and 1.5 models
"""

import asyncio
from typing import List, Optional, Dict, Any
import structlog
from google import genai
from google.genai.types import HarmCategory, HarmBlockThreshold
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.providers.base import LLMProvider, LLMMessage, LLMResponse

logger = structlog.get_logger()

# Gemini API pricing and rate limits (as of Jan 2026)
# Pricing per 1 million tokens
GEMINI_PRICING = {
    # Gemini 3 (Latest - 2026 Default)
    "gemini-3-pro-preview": {
        "input": 2.00 / 1_000_000,      # $2.00 per 1M input tokens
        "output": 12.00 / 1_000_000,    # $12.00 per 1M output tokens
        "rpm": 5,                        # Requests per minute
        "rpd": 50,                       # Requests per day
        "tpm": 32_000,                   # Tokens per minute
    },
    "gemini-3-flash-preview": {
        "input": 0.50 / 1_000_000,      # $0.50 per 1M input tokens (2026 default)
        "output": 3.00 / 1_000_000,     # $3.00 per 1M output tokens
        "rpm": 10,
        "rpd": 500,
        "tpm": 100_000,
    },
    # Gemini 2.5 (Stable Production)
    "gemini-2.5-pro": {
        "input": 1.25 / 1_000_000,      # $1.25 per 1M input tokens
        "output": 10.00 / 1_000_000,    # $10.00 per 1M output tokens
        "rpm": 5,
        "rpd": 50,
        "tpm": 32_000,
    },
    "gemini-2.5-flash": {
        "input": 0.15 / 1_000_000,      # $0.15 per 1M input tokens
        "output": 0.60 / 1_000_000,     # $0.60 per 1M output tokens
        "rpm": 10,
        "rpd": 50,
        "tpm": 100_000,
    },
    "gemini-2.5-flash-lite": {
        "input": 0.10 / 1_000_000,      # $0.10 per 1M input tokens (best for free tier)
        "output": 0.40 / 1_000_000,     # $0.40 per 1M output tokens
        "rpm": 15,
        "rpd": 1_000,                    # 1,000 requests per day
        "tpm": 250_000,
    },
    # Gemini 2.0 (Legacy)
    "gemini-2.0-flash": {
        "input": 0.10 / 1_000_000,
        "output": 0.40 / 1_000_000,
        "rpm": 15,
        "rpd": 500,
        "tpm": 100_000,
    },
    # Gemini 1.5 (Deprecated, for backward compatibility)
    "gemini-1.5-flash": {
        "input": 0.075 / 1_000_000,
        "output": 0.30 / 1_000_000,
        "rpm": 10,
        "rpd": 50,
        "tpm": 100_000,
    },
    "gemini-1.5-pro": {
        "input": 1.25 / 1_000_000,
        "output": 5.00 / 1_000_000,
        "rpm": 5,
        "rpd": 50,
        "tpm": 32_000,
    },
    "gemini-1.0-pro": {
        "input": 0.5 / 1_000_000,
        "output": 1.5 / 1_000_000,
        "rpm": 5,
        "rpd": 50,
        "tpm": 32_000,
    },
}

# Rate limit constants
RATE_LIMIT_WARNING_THRESHOLD = 0.8  # Warn at 80% of rate limit
RATE_LIMIT_RETRY_DELAY = 60  # Wait 60 seconds on rate limit error

# Gemini embedding pricing
# Gemini embedding models are free
GEMINI_EMBEDDING_PRICING = {
    "embedding-001": 0.0,  # Free tier
}


class GeminiProvider(LLMProvider):
    """Google Gemini LLM Provider
    
    Uses the new unified google.genai.Client syntax (v1.0+)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Gemini provider
        
        Args:
            config: Configuration dictionary with:
                - api_key: Gemini API key
                - model: Model name (e.g., 'gemini-2.5-flash', 'gemini-3-flash-preview')
                - temperature: Sampling temperature (0-1)
                - max_tokens: Maximum tokens in response
                - timeout_seconds: API timeout
        """
        super().__init__(config)
        
        self.api_key = config.get("api_key") or config.get("gemini_api_key")
        self.model = config.get("model", "gemini-2.5-flash")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 1000)
        self.timeout_seconds = config.get("timeout_seconds", 30)
        
        # Initialize Gemini client with new unified syntax
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            logger.warning("gemini_api_key_not_configured")
            self.client = None
        
        # Safety settings (allow all content for development)
        self.safety_settings = [
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
        
        logger.info(
            "gemini_provider_initialized",
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            sdk_version="unified_client",
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((Exception,)),
    )
    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from Gemini using new Client syntax
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (overrides config)
            max_tokens: Max tokens in response (overrides config)
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse with generated content and token counts
            
        Raises:
            ValueError: If API key not configured
            Exception: If API call fails after retries
        """
        if not self.client:
            raise ValueError("Gemini API key not configured")
        
        # Use provided values or fallback to config
        temp = temperature if temperature is not None else self.temperature
        max_toks = max_tokens if max_tokens is not None else self.max_tokens
        
        logger.info(
            "gemini_generate_start",
            num_messages=len(messages),
            model=self.model,
        )
        
        try:
            # Convert messages to Gemini format
            gemini_messages = self._convert_messages(messages)
            
            # Run async call using new Client.models.generate_content() syntax
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.client.models.generate_content(
                        model=self.model,
                        contents=gemini_messages,
                        config=genai.types.GenerateContentConfig(
                            temperature=temp,
                            max_output_tokens=max_toks,
                            safety_settings=self.safety_settings,
                        ),
                    ),
                ),
                timeout=self.timeout_seconds,
            )
            
            # Extract response text
            content = response.text if response.text else ""
            
            # Get token counts from usage metadata
            prompt_tokens = response.usage_metadata.input_token_count
            completion_tokens = response.usage_metadata.output_token_count
            
            # Calculate cost
            cost = self._calculate_cost(prompt_tokens, completion_tokens)
            
            logger.info(
                "gemini_generate_success",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_cents=cost * 100,
            )
            
            return LLMResponse(
                content=content,
                model=self.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                stop_reason=response.candidates[0].finish_reason.name if response.candidates else "UNKNOWN",
                cost_cents=cost * 100,  # Convert to cents
            )
            
        except asyncio.TimeoutError:
            logger.error("gemini_timeout", timeout=self.timeout_seconds)
            raise
        except Exception as e:
            logger.error("gemini_generation_failed", error=str(e), exc_type=type(e).__name__)
            raise
    
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings using Gemini embedding model
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values (768-dim for Gemini embedding models)
            
        Raises:
            ValueError: If API key not configured
        """
        if not self.api_key:
            raise ValueError("Gemini API key not configured")
        
        logger.info("gemini_embed_start", text_length=len(text))
        
        try:
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.client.models.embed_content(
                        model="text-embedding-004",
                        contents=text,
                    ),
                ),
                timeout=self.timeout_seconds,
            )
            
            embedding = response.embedding
            logger.info("gemini_embed_success", embedding_dim=len(embedding))
            
            return embedding
            
        except asyncio.TimeoutError:
            logger.error("gemini_embed_timeout", timeout=self.timeout_seconds)
            raise
        except Exception as e:
            logger.error("gemini_embed_failed", error=str(e))
            raise
    
    async def health_check(self) -> bool:
        """Check Gemini API connectivity using new Client syntax
        
        Returns:
            True if API is accessible, False otherwise
        """
        if not self.client:
            logger.warning("gemini_health_check_no_client")
            return False
        
        try:
            logger.info("gemini_health_check_start")
            
            # Try a simple generate call with new Client syntax
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.client.models.generate_content(
                        model=self.model,
                        contents="Say 'ok'",
                        config=genai.types.GenerateContentConfig(
                            temperature=0.0,
                            max_output_tokens=10,
                        ),
                    ),
                ),
                timeout=10,
            )
            
            is_healthy = response and response.text
            logger.info("gemini_health_check_complete", healthy=is_healthy)
            
            return is_healthy
            
        except Exception as e:
            logger.error("gemini_health_check_failed", error=str(e))
            return False
    
    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for API call in USD cents
        
        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            
        Returns:
            Cost in USD cents
        """
        pricing = GEMINI_PRICING.get(self.model, {})
        input_cost = prompt_tokens * pricing.get("input", 0)
        output_cost = completion_tokens * pricing.get("output", 0)
        total_cost = input_cost + output_cost
        
        return total_cost * 100  # Convert to cents
    
    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost in USD (not cents)"""
        pricing = GEMINI_PRICING.get(self.model, {})
        input_cost = prompt_tokens * pricing.get("input", 0)
        output_cost = completion_tokens * pricing.get("output", 0)
        
        return input_cost + output_cost
    
    @staticmethod
    def _convert_messages(messages: List[LLMMessage]) -> str:
        """Convert LLMMessage list to Gemini format
        
        Gemini expects a single text prompt, so we concatenate messages
        with role indicators.
        
        Args:
            messages: List of LLMMessage objects
            
        Returns:
            Formatted string for Gemini API
        """
        parts = []
        
        for msg in messages:
            if msg.role == "system":
                parts.append(f"[SYSTEM]: {msg.content}")
            elif msg.role == "user":
                parts.append(f"[USER]: {msg.content}")
            elif msg.role == "assistant":
                parts.append(f"[ASSISTANT]: {msg.content}")
            else:
                parts.append(msg.content)
        
        return "\n".join(parts)
    
    def __repr__(self) -> str:
        return f"GeminiProvider(model={self.model}, api_key={'configured' if self.api_key else 'not_configured'})"
