# intelligence/service/app/agents/base.py
"""Base agent class - Abstract interface for all agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import structlog

from app.loaders import get_agent_loader, get_prompt_loader
from app.prompt_engine import get_template_renderer
from app.providers.manager import get_provider_router

logger = structlog.get_logger()


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(self, agent_name: str):
        """Initialize base agent.
        
        Args:
            agent_name: Name of the agent (must match YAML config file)
        """
        self.agent_name = agent_name
        self.agent_loader = get_agent_loader()
        self.prompt_loader = get_prompt_loader()
        self.template_renderer = get_template_renderer()
        self.provider_router = get_provider_router()
        
        # Load configuration
        self.config = self.agent_loader.get_agent_config(agent_name)
        if not self.config:
            raise ValueError(f"Agent '{agent_name}' configuration not found")
        
        logger.info("agent_initialized", agent_name=agent_name)
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent with given inputs.
        
        Args:
            inputs: Input parameters
            
        Returns:
            Agent output
        """
        logger.info("agent_execution_start", agent=self.agent_name)
        
        try:
            # Validate inputs
            self._validate_inputs(inputs)
            
            # Get prompt template name
            prompt_name = self._get_prompt_name()
            if not prompt_name:
                raise ValueError(f"No prompt template configured for {self.agent_name}")
            
            # Render prompt
            rendered_prompt = self.template_renderer.render_prompt(
                prompt_name=prompt_name,
                context=inputs
            )
            
            if not rendered_prompt:
                raise ValueError(f"Failed to render prompt template: {prompt_name}")
            
            # Get routing configuration
            routing = self._get_routing_config()
            
            # Call LLM provider
            from app.providers.base import LLMMessage
            
            messages = [LLMMessage(role="user", content=rendered_prompt)]
            
            response = await self.provider_router.generate(
                messages=messages,
                provider=routing["provider"],
                temperature=routing["temperature"],
                max_tokens=routing["max_tokens"],
            )
            
            # Parse and return output
            output = self._parse_response(response.content)
            
            logger.info(
                "agent_execution_complete",
                agent=self.agent_name,
                cost_cents=response.cost_cents,
            )
            
            return output
            
        except Exception as e:
            logger.error("agent_execution_failed", agent=self.agent_name, error=str(e))
            raise
    
    def _get_prompt_name(self) -> Optional[str]:
        """Get prompt template name from configuration.
        
        Returns:
            Prompt name or None
        """
        return self.config.get("prompt_template")
    
    def _get_routing_config(self) -> Dict[str, Any]:
        """Get routing configuration from agent config.
        
        Returns:
            Routing configuration dict
        """
        routing = self.config.get("routing", {})
        return {
            "provider": routing.get("provider", "gemini"),
            "model": routing.get("model", "gemini-3-flash-preview"),
            "temperature": routing.get("temperature", 0.7),
            "max_tokens": routing.get("max_tokens", 1000),
        }
    
    @abstractmethod
    def _validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """Validate agent inputs - subclasses must implement.
        
        Args:
            inputs: Input parameters to validate
            
        Raises:
            ValueError: If inputs are invalid
        """
        pass
    
    @abstractmethod
    def _parse_response(self, response_content: str) -> Dict[str, Any]:
        """Parse LLM response - subclasses must implement.
        
        Args:
            response_content: Raw LLM response
            
        Returns:
            Parsed output dictionary
        """
        pass
