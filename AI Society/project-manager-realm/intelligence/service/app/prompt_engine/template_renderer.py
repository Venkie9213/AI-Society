# intelligence/service/app/prompt_engine/template_renderer.py
"""Template rendering engine - Jinja2-based prompt rendering."""

from typing import Dict, Any, Optional
from jinja2 import Template, TemplateError
import structlog

from app.loaders import get_prompt_loader

logger = structlog.get_logger()


class TemplateRenderer:
    """Renders Jinja2 prompt templates with given context."""
    
    def __init__(self):
        """Initialize template renderer."""
        self.prompt_loader = get_prompt_loader()
        logger.info("template_renderer_initialized")
    
    def render_prompt(
        self,
        prompt_name: str,
        context: Dict[str, Any],
    ) -> Optional[str]:
        """Render a prompt template with given context.
        
        Args:
            prompt_name: Name of the prompt template
            context: Variables to interpolate into template
            
        Returns:
            Rendered prompt string or None if template not found
        """
        logger.info("rendering_prompt", prompt_name=prompt_name)
        
        # Load template
        template_str = self.prompt_loader.get_prompt_template(prompt_name)
        
        if not template_str:
            logger.error("prompt_template_not_found", prompt_name=prompt_name)
            return None
        
        try:
            # Create Jinja2 template
            template = Template(template_str)
            
            # Render with context
            rendered = template.render(**context)
            
            logger.info(
                "prompt_rendered",
                prompt_name=prompt_name,
                context_keys=list(context.keys())
            )
            
            return rendered
            
        except TemplateError as e:
            logger.error(
                "template_render_failed",
                prompt_name=prompt_name,
                error=str(e)
            )
            return None
        except Exception as e:
            logger.error(
                "unexpected_render_error",
                prompt_name=prompt_name,
                error=str(e)
            )
            return None
    
    def validate_template(self, prompt_name: str) -> bool:
        """Validate a prompt template without rendering.
        
        Args:
            prompt_name: Name of the prompt template
            
        Returns:
            True if template is valid, False otherwise
        """
        template_str = self.prompt_loader.get_prompt_template(prompt_name)
        
        if not template_str:
            return False
        
        try:
            Template(template_str)
            return True
        except TemplateError as e:
            logger.error(
                "template_validation_failed",
                prompt_name=prompt_name,
                error=str(e)
            )
            return False
    
    def get_template_variables(self, prompt_name: str) -> set:
        """Get all variables used in a template.
        
        Args:
            prompt_name: Name of the prompt template
            
        Returns:
            Set of variable names
        """
        template_str = self.prompt_loader.get_prompt_template(prompt_name)
        
        if not template_str:
            return set()
        
        try:
            template = Template(template_str)
            # Extract variable names from the Abstract Syntax Tree
            variables = set()
            
            for node in template.module.__dict__.get('root', []):
                if hasattr(node, 'nodes'):
                    for child in node.nodes:
                        if hasattr(child, 'name'):
                            variables.add(child.name)
            
            return variables
        except Exception as e:
            logger.error(
                "template_variable_extraction_failed",
                prompt_name=prompt_name,
                error=str(e)
            )
            return set()


# Global template renderer instance
_template_renderer: Optional[TemplateRenderer] = None


def get_template_renderer() -> TemplateRenderer:
    """Get or create global template renderer instance.
    
    Returns:
        TemplateRenderer instance
    """
    global _template_renderer
    
    if _template_renderer is None:
        _template_renderer = TemplateRenderer()
    
    return _template_renderer
