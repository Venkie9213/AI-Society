# intelligence/service/app/agents/clarification_agent.py
"""Clarification agent - generates clarifying questions."""

from typing import Dict, Any
import json
import structlog

from app.agents.base import BaseAgent

logger = structlog.get_logger()


class ClarificationAgent(BaseAgent):
    """Agent for generating clarifying questions from initial requirements."""
    
    def __init__(self):
        """Initialize clarification agent."""
        super().__init__("clarification-agent")
    
    def _validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """Validate clarification agent inputs.
        
        Args:
            inputs: Input parameters
            
        Raises:
            ValueError: If required inputs are missing
        """
        required_fields = ["user_description", "project_context"]
        
        for field in required_fields:
            if field not in inputs:
                raise ValueError(f"Missing required input: {field}")
            
            if not isinstance(inputs[field], str):
                raise ValueError(f"{field} must be a string")
    
    def _parse_response(self, response_content: str) -> Dict[str, Any]:
        """Parse clarification agent response.
        
        Args:
            response_content: Raw LLM response (expected to be JSON)
            
        Returns:
            Parsed output with questions and metadata
        """
        try:
            output = json.loads(response_content)
            
            # Validate output structure
            if "questions" not in output:
                output["questions"] = []
            
            if "rationale" not in output:
                output["rationale"] = "Clarification questions generated"
            
            if "estimated_confidence" not in output:
                output["estimated_confidence"] = 0.5
            
            return output
            
        except json.JSONDecodeError as e:
            logger.error("clarification_response_parse_failed", error=str(e))
            return {
                "questions": [],
                "rationale": f"Failed to parse response: {str(e)}",
                "estimated_confidence": 0.0,
            }
