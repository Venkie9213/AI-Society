# intelligence/service/app/agents/prd_generator_agent.py
"""PRD generator agent - converts requirements to formal PRD."""

from typing import Dict, Any
import json
import structlog

from app.agents.base import BaseAgent

logger = structlog.get_logger()


class PRDGeneratorAgent(BaseAgent):
    """Agent for generating formal PRDs from clarified requirements."""
    
    def __init__(self):
        """Initialize PRD generator agent."""
        super().__init__("prd-generator-agent")
    
    def _validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """Validate PRD generator agent inputs.
        
        Args:
            inputs: Input parameters
            
        Raises:
            ValueError: If required inputs are missing
        """
        required_fields = ["requirement_description", "clarification_answers"]
        
        for field in required_fields:
            if field not in inputs:
                raise ValueError(f"Missing required input: {field}")
        
        if not isinstance(inputs["requirement_description"], str):
            raise ValueError("requirement_description must be a string")
        
        if not isinstance(inputs["clarification_answers"], list):
            raise ValueError("clarification_answers must be a list")
    
    def _parse_response(self, response_content: str) -> Dict[str, Any]:
        """Parse PRD generator agent response.
        
        Args:
            response_content: Raw LLM response (expected to be JSON with PRD)
            
        Returns:
            Parsed PRD output
        """
        try:
            output = json.loads(response_content)
            
            # Validate PRD structure
            if "prd" not in output:
                output["prd"] = {}
            
            # Ensure required PRD sections exist
            prd = output["prd"]
            required_sections = [
                "title", "overview", "objectives", "user_stories",
                "acceptance_criteria", "requirements", "scope",
                "technical_considerations", "timeline", "success_metrics"
            ]
            
            for section in required_sections:
                if section not in prd:
                    prd[section] = None
            
            # Add metadata
            output["completeness_score"] = self._calculate_completeness(prd)
            output["estimated_effort"] = prd.get("estimated_effort", "Unknown")
            
            return output
            
        except json.JSONDecodeError as e:
            logger.error("prd_response_parse_failed", error=str(e))
            return {
                "prd": {},
                "completeness_score": 0.0,
                "estimated_effort": "Failed to generate PRD",
            }
    
    def _calculate_completeness(self, prd: Dict[str, Any]) -> float:
        """Calculate PRD completeness score.
        
        Args:
            prd: PRD dictionary
            
        Returns:
            Completeness score (0-1)
        """
        required_sections = [
            "title", "overview", "objectives", "user_stories",
            "acceptance_criteria", "requirements", "scope",
            "technical_considerations", "timeline", "success_metrics"
        ]
        
        filled_sections = sum(1 for section in required_sections if prd.get(section))
        return filled_sections / len(required_sections)
