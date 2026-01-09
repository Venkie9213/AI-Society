# app/providers/router.py
"""Provider Router - Manages LLM provider selection and fallback"""

from typing import List, Optional, Dict, Any, Union
from enum import Enum
import structlog

from app.providers.base import LLMProvider, LLMMessage, LLMResponse
from app.providers.gemini import GeminiProvider

logger = structlog.get_logger()


class ProviderType(str, Enum):
    """Available LLM providers"""
    GEMINI = "gemini"
    CLAUDE = "claude"
    GPT4 = "gpt4"


class ProviderRouter:
    """Routes LLM requests to appropriate provider with fallback logic"""
    
    def __init__(self, config: Union[Dict[str, Any], Any]):
        """Initialize provider router
        
        Args:
            config: Configuration dict or AppConfig object containing:
                - primary_provider: Primary provider to use
                - fallback_providers: List of fallback providers in order
                - provider_configs: Dict of provider-specific configs
                - default_provider: Default provider (if not primary_provider)
                - default_model: Default model
        """
        self.config = config
        
        # Support both dict and AppConfig object
        def _get(key: str, default: Any = None) -> Any:
            if isinstance(config, dict):
                return config.get(key, default)
            else:
                return getattr(config, key, default)
        
        self._get = _get  # Store for use in other methods
        
        self.primary_provider = _get("primary_provider") or _get("default_provider", "gemini")
        self.fallback_providers = _get("fallback_providers", ["gemini"])
        if not isinstance(self.fallback_providers, list):
            self.fallback_providers = ["gemini"]
        self.provider_configs = _get("provider_configs", {})
        
        # Initialize providers
        self.providers: Dict[str, LLMProvider] = {}
        self._initialize_providers()
        
        logger.info(
            "provider_router_initialized",
            primary=self.primary_provider,
            fallbacks=self.fallback_providers,
        )
    
    def _initialize_providers(self) -> None:
        """Initialize all available providers"""
        
        # Initialize Gemini
        if "gemini" in self.fallback_providers or self.primary_provider == "gemini":
            try:
                # Get provider config, defaulting to AppConfig values if not in provider_configs
                if isinstance(self.provider_configs, dict):
                    gemini_config = self.provider_configs.get("gemini", {})
                else:
                    gemini_config = {}
                
                # Add fallback values from AppConfig if using AppConfig
                if hasattr(self.config, 'gemini_api_key'):
                    if not gemini_config.get("api_key") and not gemini_config.get("gemini_api_key"):
                        gemini_config = dict(gemini_config)  # Make copy
                        gemini_config["gemini_api_key"] = self.config.gemini_api_key
                    if not gemini_config.get("model"):
                        gemini_config["model"] = self.config.gemini_model
                
                self.providers["gemini"] = GeminiProvider(gemini_config)
                logger.info("gemini_provider_loaded")
            except Exception as e:
                logger.error("gemini_provider_load_failed", error=str(e))
    
    async def generate(
        self,
        messages: List[LLMMessage],
        provider: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response with automatic fallback
        
        Args:
            messages: Conversation messages
            provider: Specific provider to use (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse from first successful provider
            
        Raises:
            Exception: If all providers fail
        """
        # Determine provider sequence to try
        if provider:
            provider_sequence = [provider]
        else:
            provider_sequence = [self.primary_provider] + [
                p for p in self.fallback_providers 
                if p != self.primary_provider
            ]
        
        logger.info(
            "provider_generate_start",
            provider_sequence=provider_sequence,
            num_messages=len(messages),
        )
        
        last_error = None
        
        for provider_name in provider_sequence:
            if provider_name not in self.providers:
                logger.warning("provider_not_available", provider=provider_name)
                continue
            
            try:
                provider_instance = self.providers[provider_name]
                logger.info("provider_generate_attempt", provider=provider_name)
                
                response = await provider_instance.generate(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                logger.info(
                    "provider_generate_success",
                    provider=provider_name,
                    cost_cents=response.cost_cents,
                )
                
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(
                    "provider_generate_failed",
                    provider=provider_name,
                    error=str(e),
                    exc_type=type(e).__name__,
                )
                continue
        
        # All providers failed
        error_msg = f"All providers failed. Last error: {str(last_error)}"
        logger.error("all_providers_failed", error=error_msg)
        raise Exception(error_msg)
    
    async def embed(
        self,
        text: str,
        provider: Optional[str] = None,
    ) -> List[float]:
        """Generate embeddings with automatic fallback
        
        Args:
            text: Text to embed
            provider: Specific provider to use (optional)
            
        Returns:
            Embedding from first successful provider
            
        Raises:
            Exception: If all providers fail
        """
        if provider:
            provider_sequence = [provider]
        else:
            provider_sequence = [self.primary_provider] + [
                p for p in self.fallback_providers 
                if p != self.primary_provider
            ]
        
        logger.info(
            "provider_embed_start",
            provider_sequence=provider_sequence,
            text_length=len(text),
        )
        
        last_error = None
        
        for provider_name in provider_sequence:
            if provider_name not in self.providers:
                logger.warning("provider_not_available_for_embed", provider=provider_name)
                continue
            
            try:
                provider_instance = self.providers[provider_name]
                logger.info("provider_embed_attempt", provider=provider_name)
                
                embedding = await provider_instance.embed(text)
                
                logger.info(
                    "provider_embed_success",
                    provider=provider_name,
                    embedding_dim=len(embedding),
                )
                
                return embedding
                
            except Exception as e:
                last_error = e
                logger.warning(
                    "provider_embed_failed",
                    provider=provider_name,
                    error=str(e),
                )
                continue
        
        # All providers failed
        error_msg = f"All embedding providers failed. Last error: {str(last_error)}"
        logger.error("all_embed_providers_failed", error=error_msg)
        raise Exception(error_msg)
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all providers
        
        Returns:
            Dictionary mapping provider names to health status
        """
        logger.info("provider_health_check_start", providers=list(self.providers.keys()))
        
        health_status = {}
        
        for provider_name, provider_instance in self.providers.items():
            try:
                is_healthy = await provider_instance.health_check()
                health_status[provider_name] = is_healthy
                logger.info(
                    "provider_health_status",
                    provider=provider_name,
                    healthy=is_healthy,
                )
            except Exception as e:
                health_status[provider_name] = False
                logger.error(
                    "provider_health_check_error",
                    provider=provider_name,
                    error=str(e),
                )
        
        return health_status
    
    def get_primary_provider(self) -> Optional[LLMProvider]:
        """Get primary provider instance
        
        Returns:
            Primary provider or None if not available
        """
        return self.providers.get(self.primary_provider)
    
    def get_provider(self, name: str) -> Optional[LLMProvider]:
        """Get specific provider instance
        
        Args:
            name: Provider name
            
        Returns:
            Provider instance or None if not available
        """
        return self.providers.get(name)
    
    def list_providers(self) -> List[str]:
        """List available providers
        
        Returns:
            List of provider names
        """
        return list(self.providers.keys())
    
    def __repr__(self) -> str:
        return (
            f"ProviderRouter(primary={self.primary_provider}, "
            f"available={list(self.providers.keys())})"
        )
