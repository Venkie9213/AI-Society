# intelligence/service/app/loaders/prompt_loader.py
"""Prompt template loader - loads from prompts/**/*.yaml."""

from typing import Dict, Any, Optional
from pathlib import Path
import yaml
import structlog

from app.loaders.base_loader import BaseLoader
from app.config import Settings

logger = structlog.get_logger()


class PromptLoader(BaseLoader):
    """Loads prompt templates from intelligence/prompts/ directory."""
    
    def __init__(self, settings: Settings, cache_enabled: bool = True):
        """Initialize prompt loader.
        
        Args:
            settings: Application settings
            cache_enabled: Whether to enable caching
        """
        super().__init__(cache_enabled=cache_enabled)
        self.settings = settings
        self.prompts_path = settings.prompts_path
    
    def load_prompts(self) -> Dict[str, str]:
        """Load all prompt templates recursively.
        
        Returns:
            Dictionary mapping prompt names to template strings
        """
        cached = self._get_cached("prompts")
        if cached is not None:
            return cached
        
        prompts = {}
        
        if not self.prompts_path.exists():
            logger.warning("prompts_path_not_found", path=str(self.prompts_path))
            return prompts
        
        try:
            # Rglob for *.prompt.yaml files recursively
            prompt_files = list(self.prompts_path.rglob("*.prompt.yaml"))
            
            for prompt_file in prompt_files:
                # Create prompt name from relative path
                relative_path = prompt_file.relative_to(self.prompts_path)
                prompt_name = str(relative_path.with_suffix("")).replace("/", "_")
                
                try:
                    with open(prompt_file, "r") as f:
                        config = yaml.safe_load(f)
                    
                    # Extract template string
                    template = config.get("template", "")
                    prompts[prompt_name] = template
                    
                    logger.info("prompt_loaded", prompt_name=prompt_name)
                    
                except Exception as e:
                    logger.error(
                        "prompt_load_failed",
                        prompt_name=prompt_name,
                        error=str(e)
                    )
            
            self._set_cache("prompts", prompts)
            return prompts
            
        except Exception as e:
            logger.error("prompts_load_failed", error=str(e))
            return prompts
    
    def get_prompt_template(self, prompt_name: str) -> Optional[str]:
        """Get specific prompt template.
        
        Args:
            prompt_name: Prompt identifier (e.g., "prd-generator")
            
        Returns:
            Template string or None
        """
        prompts = self.load_prompts()
        
        if prompt_name not in prompts:
            logger.warning("prompt_not_found", prompt_name=prompt_name)
            return None
        
        return prompts[prompt_name]
    
    def list_prompts(self) -> list:
        """List all available prompt names.
        
        Returns:
            List of prompt names
        """
        prompts = self.load_prompts()
        return list(prompts.keys())


# Global prompt loader instance
_prompt_loader: Optional[PromptLoader] = None


def get_prompt_loader(settings: Optional[Settings] = None) -> PromptLoader:
    """Get or create global prompt loader instance.
    
    Args:
        settings: Optional settings instance
        
    Returns:
        PromptLoader instance
    """
    global _prompt_loader
    
    if _prompt_loader is None:
        from app.config import get_settings
        settings = settings or get_settings()
        _prompt_loader = PromptLoader(settings)
    
    return _prompt_loader
