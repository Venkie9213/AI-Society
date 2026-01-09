# app/providers/__init__.py
"""LLM Providers package

Organized modules:
- base: LLMProvider abstract base class and message types
- implementations/: Concrete LLM provider implementations
  - gemini: Google Gemini provider
- policies/: Provider policies and configurations
  - safety: Safety policy management
  - pricing: Pricing and quota management
- factory: Provider factory for dependency injection
- router: Provider router for multi-provider support
- manager: Global provider manager
"""

from app.providers.factory import ProviderFactory, get_provider_factory
from app.providers.policies import SafetyPolicyFactory, PricingConfig, ModelPricing

__all__ = [
    "base",
    "implementations",
    "policies",
    "router",
    "factory",
    "manager",
    "ProviderFactory",
    "get_provider_factory",
    "SafetyPolicyFactory",
    "PricingConfig",
    "ModelPricing",
]
