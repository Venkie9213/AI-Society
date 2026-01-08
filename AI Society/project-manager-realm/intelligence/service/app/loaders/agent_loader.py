# intelligence/service/app/loaders/agent_loader.py
"""Agent configuration loader - loads from agents/*.yaml."""

from typing import Dict, Any, Optional
from pathlib import Path
import yaml
import structlog

from app.loaders.base_loader import BaseLoader
from app.config import Settings

logger = structlog.get_logger()


class AgentLoader(BaseLoader):
    """Loads agent configurations from intelligence/agents/ directory."""
    
    def __init__(self, settings: Settings, cache_enabled: bool = True):
        """Initialize agent loader.
        
        Args:
            settings: Application settings
            cache_enabled: Whether to enable caching
        """
        super().__init__(cache_enabled=cache_enabled)
        self.settings = settings
        self.agents_path = settings.agents_path
    
    def load_agents(self) -> Dict[str, Any]:
        """Load all agent configurations.
        
        Returns:
            Dictionary mapping agent names to configurations
        """
        cached = self._get_cached("agents")
        if cached is not None:
            return cached
        
        agents = {}
        
        if not self.agents_path.exists():
            logger.warning("agents_path_not_found", path=str(self.agents_path))
            return agents
        
        try:
            # Glob for *.yaml files (not directories)
            agent_files = [
                f for f in self.agents_path.glob("*.yaml")
                if f.is_file() and f.name != "README.md"
            ]
            
            for agent_file in agent_files:
                agent_name = agent_file.stem  # filename without extension
                
                try:
                    with open(agent_file, "r") as f:
                        agent_config = yaml.safe_load(f)
                    
                    agents[agent_name] = agent_config
                    logger.info("agent_loaded", agent_name=agent_name)
                    
                except Exception as e:
                    logger.error(
                        "agent_load_failed",
                        agent_name=agent_name,
                        error=str(e)
                    )
            
            self._set_cache("agents", agents)
            return agents
            
        except Exception as e:
            logger.error("agents_load_failed", error=str(e))
            return agents
    
    def get_agent_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get specific agent configuration.
        
        Args:
            agent_name: Agent identifier (e.g., "clarification-agent")
            
        Returns:
            Agent configuration or None
        """
        agents = self.load_agents()
        
        if agent_name not in agents:
            logger.warning("agent_not_found", agent_name=agent_name)
            return None
        
        return agents[agent_name]
    
    def list_agents(self) -> list:
        """List all available agent names.
        
        Returns:
            List of agent names
        """
        agents = self.load_agents()
        return list(agents.keys())


# Global agent loader instance
_agent_loader: Optional[AgentLoader] = None


def get_agent_loader(settings: Optional[Settings] = None) -> AgentLoader:
    """Get or create global agent loader instance.
    
    Args:
        settings: Optional settings instance
        
    Returns:
        AgentLoader instance
    """
    global _agent_loader
    
    if _agent_loader is None:
        from app.config import get_settings
        settings = settings or get_settings()
        _agent_loader = AgentLoader(settings)
    
    return _agent_loader
