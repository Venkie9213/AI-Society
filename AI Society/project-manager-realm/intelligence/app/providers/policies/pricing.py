"""LLM Provider pricing and quota management.

Centralizes pricing data and rate limit configurations for all providers.
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class ModelPricing:
    """Model pricing information."""
    
    input_cost_per_million: float  # Cost per 1M input tokens
    output_cost_per_million: float  # Cost per 1M output tokens
    requests_per_minute: int  # RPM limit
    requests_per_day: int  # RPD limit
    tokens_per_minute: int  # TPM limit


class PricingConfig:
    """Centralized pricing configuration for all LLM providers."""
    
    # Gemini 3 (Latest - 2026)
    GEMINI_3_PRO_PREVIEW = ModelPricing(
        input_cost_per_million=2.00,
        output_cost_per_million=12.00,
        requests_per_minute=5,
        requests_per_day=50,
        tokens_per_minute=32_000,
    )
    
    GEMINI_3_FLASH_PREVIEW = ModelPricing(
        input_cost_per_million=0.50,
        output_cost_per_million=3.00,
        requests_per_minute=10,
        requests_per_day=500,
        tokens_per_minute=100_000,
    )
    
    # Gemini 2.5 (Stable Production)
    GEMINI_2_5_PRO = ModelPricing(
        input_cost_per_million=1.25,
        output_cost_per_million=10.00,
        requests_per_minute=5,
        requests_per_day=50,
        tokens_per_minute=32_000,
    )
    
    GEMINI_2_5_FLASH = ModelPricing(
        input_cost_per_million=0.15,
        output_cost_per_million=0.60,
        requests_per_minute=10,
        requests_per_day=50,
        tokens_per_minute=100_000,
    )
    
    GEMINI_2_5_FLASH_LITE = ModelPricing(
        input_cost_per_million=0.10,
        output_cost_per_million=0.40,
        requests_per_minute=15,
        requests_per_day=1_000,
        tokens_per_minute=250_000,
    )
    
    # Gemini 2.0 (Legacy)
    GEMINI_2_0_FLASH = ModelPricing(
        input_cost_per_million=0.10,
        output_cost_per_million=0.40,
        requests_per_minute=15,
        requests_per_day=500,
        tokens_per_minute=100_000,
    )
    
    # Gemini 1.5 (Deprecated)
    GEMINI_1_5_FLASH = ModelPricing(
        input_cost_per_million=0.075,
        output_cost_per_million=0.30,
        requests_per_minute=10,
        requests_per_day=50,
        tokens_per_minute=100_000,
    )
    
    GEMINI_1_5_PRO = ModelPricing(
        input_cost_per_million=1.25,
        output_cost_per_million=5.00,
        requests_per_minute=5,
        requests_per_day=50,
        tokens_per_minute=32_000,
    )
    
    GEMINI_1_0_PRO = ModelPricing(
        input_cost_per_million=0.5,
        output_cost_per_million=1.5,
        requests_per_minute=5,
        requests_per_day=50,
        tokens_per_minute=32_000,
    )
    
    # Pricing lookup by model name
    MODEL_PRICES: Dict[str, ModelPricing] = {
        "gemini-3-pro-preview": GEMINI_3_PRO_PREVIEW,
        "gemini-3-flash-preview": GEMINI_3_FLASH_PREVIEW,
        "gemini-2.5-pro": GEMINI_2_5_PRO,
        "gemini-2.5-flash": GEMINI_2_5_FLASH,
        "gemini-2.5-flash-lite": GEMINI_2_5_FLASH_LITE,
        "gemini-2.0-flash": GEMINI_2_0_FLASH,
        "gemini-1.5-flash": GEMINI_1_5_FLASH,
        "gemini-1.5-pro": GEMINI_1_5_PRO,
        "gemini-1.0-pro": GEMINI_1_0_PRO,
    }
    
    # Rate limit constants
    RATE_LIMIT_WARNING_THRESHOLD = 0.8  # Warn at 80% utilization
    RATE_LIMIT_RETRY_DELAY = 60  # Seconds to wait on rate limit
    
    @classmethod
    def get_pricing(cls, model_name: str) -> ModelPricing:
        """Get pricing for a model.
        
        Args:
            model_name: Model identifier
            
        Returns:
            ModelPricing instance
            
        Raises:
            ValueError: If model not found
        """
        pricing = cls.MODEL_PRICES.get(model_name)
        if pricing is None:
            raise ValueError(f"Unknown model: {model_name}")
        return pricing
    
    @classmethod
    def calculate_cost(cls, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for API call.
        
        Args:
            model_name: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        pricing = cls.get_pricing(model_name)
        input_cost = (input_tokens / 1_000_000) * pricing.input_cost_per_million
        output_cost = (output_tokens / 1_000_000) * pricing.output_cost_per_million
        return input_cost + output_cost
