# app/providers/implementations/gemini.py
"""Google Gemini LLM Provider Implementation

Uses google.genai.Client (v1.0+) for Gemini 3, 2.5, and 1.5 models.
"""

import asyncio
from typing import List, Optional, Dict, Any
import structlog
from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.providers.base import LLMProvider, LLMMessage, LLMResponse
from app.providers.policies.safety import SafetyPolicyFactory
from app.providers.policies.pricing import PricingConfig

logger = structlog.get_logger()


class GeminiProvider(LLMProvider):
    """Google Gemini LLM Provider using google.genai.Client."""
    
    EMBEDDING_MODEL = "text-embedding-004"
    TIMEOUT_SECONDS = 30
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Gemini provider.
        
        Args:
            config: Configuration with api_key, model, temperature, max_tokens
        """
        super().__init__(config)
        
        self.api_key = config.get("api_key") or config.get("gemini_api_key")
        self.model = config.get("model", "gemini-2.5-flash")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 1000)
        
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.safety_settings = SafetyPolicyFactory.create_gemini_policy(block_none=True).get_settings()
        
        logger.info(
            "gemini_provider_initialized",
            model=self.model,
            api_configured=bool(self.api_key),
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
        """Generate response from Gemini.
        
        Args:
            messages: Conversation messages
            temperature: Sampling temperature (overrides config)
            max_tokens: Max tokens in response (overrides config)
            
        Returns:
            LLMResponse with generated content and token counts
        """
        if not self.client:
            raise ValueError("Gemini API key not configured")
        
        temp = temperature if temperature is not None else self.temperature
        max_toks = max_tokens if max_tokens is not None else self.max_tokens
        
        logger.info("gemini_generate_start", messages=len(messages), model=self.model)
        
        try:
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.client.models.generate_content(
                        model=self.model,
                        contents=self._format_messages(messages),
                        config=genai.types.GenerateContentConfig(
                            temperature=temp,
                            max_output_tokens=max_toks,
                            safety_settings=self.safety_settings,
                        ),
                    ),
                ),
                timeout=self.TIMEOUT_SECONDS,
            )
            
            content = response.text or ""
            tokens = self._extract_tokens(response)
            cost = PricingConfig.calculate_cost(self.model, tokens["prompt"], tokens["completion"])
            
            logger.info(
                "gemini_generate_success",
                prompt_tokens=tokens["prompt"],
                completion_tokens=tokens["completion"],
                cost_usd=cost,
            )
            
            return LLMResponse(
                content=content,
                model=self.model,
                prompt_tokens=tokens["prompt"],
                completion_tokens=tokens["completion"],
                stop_reason=self._get_finish_reason(response),
                cost_cents=cost * 100,
            )
            
        except asyncio.TimeoutError:
            logger.error("gemini_timeout", timeout=self.TIMEOUT_SECONDS)
            raise
        except Exception as e:
            logger.error("gemini_generation_failed", error=str(e), exc_type=type(e).__name__)
            raise
    
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings using Gemini embedding model.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
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
                        model=self.EMBEDDING_MODEL,
                        contents=text,
                    ),
                ),
                timeout=self.TIMEOUT_SECONDS,
            )
            
            logger.info("gemini_embed_success", embedding_dim=len(response.embedding))
            return response.embedding
            
        except asyncio.TimeoutError:
            logger.error("gemini_embed_timeout", timeout=self.TIMEOUT_SECONDS)
            raise
        except Exception as e:
            logger.error("gemini_embed_failed", error=str(e))
            raise
    
    async def health_check(self) -> bool:
        """Check Gemini API connectivity.
        
        Returns:
            True if API is accessible, False otherwise
        """
        if not self.client:
            logger.warning("gemini_health_check_no_client")
            return False
        
        try:
            logger.info("gemini_health_check_start")
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
    
    @staticmethod
    def _extract_tokens(response) -> Dict[str, int]:
        """Extract token counts from response metadata.
        
        Handles different SDK versions gracefully.
        """
        prompt_tokens, completion_tokens = 0, 0
        
        usage_metadata = getattr(response, 'usage_metadata', None)
        if usage_metadata:
            prompt_tokens = (
                getattr(usage_metadata, 'input_token_count', None)
                or getattr(usage_metadata, 'prompt_token_count', 0)
            )
            completion_tokens = (
                getattr(usage_metadata, 'output_token_count', None)
                or getattr(usage_metadata, 'completion_tokens_count', None)
                or getattr(usage_metadata, 'candidate_token_count', 0)
            )
        
        return {"prompt": prompt_tokens, "completion": completion_tokens}
    
    @staticmethod
    def _get_finish_reason(response) -> str:
        """Extract finish reason from response."""
        if not response.candidates:
            return "UNKNOWN"
        
        finish_reason = response.candidates[0].finish_reason
        return (
            finish_reason
            if isinstance(finish_reason, str)
            else finish_reason.name if finish_reason else "UNKNOWN"
        )
    
    @staticmethod
    def _format_messages(messages: List[LLMMessage]) -> str:
        """Format messages for Gemini API."""
        parts = []
        for msg in messages:
            role_prefix = f"[{msg.role.upper()}]: " if hasattr(msg, 'role') else ""
            content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
            parts.append(f"{role_prefix}{content}")
        
        return "\n".join(parts)
    
    def __repr__(self) -> str:
        return (
            f"GeminiProvider(model={self.model}, "
            f"api_configured={bool(self.api_key)})"
        )
