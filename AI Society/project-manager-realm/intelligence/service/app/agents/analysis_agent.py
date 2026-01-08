# intelligence/service/app/agents/analysis_agent.py
"""Analysis agent - validates and analyzes requirements."""

from typing import Dict, Any
import json
import structlog

from app.agents.base import BaseAgent

logger = structlog.get_logger()


class AnalysisAgent(BaseAgent):
    """Agent for analyzing requirements for completeness, feasibility, and risks."""
    
    def __init__(self):
        """Initialize analysis agent."""
        super().__init__("analysis-agent")
    
    def _validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """Validate analysis agent inputs.
        
        Args:
            inputs: Input parameters
            
        Raises:
            ValueError: If required inputs are missing
        """
        if "requirements" not in inputs:
            raise ValueError("Missing required input: requirements")
        
        if not isinstance(inputs["requirements"], (dict, str)):
            raise ValueError("requirements must be a dict or string")
        
        analysis_depth = inputs.get("analysis_depth", "standard")
        valid_depths = ["quick", "standard", "deep"]
        
        if analysis_depth not in valid_depths:
            raise ValueError(f"analysis_depth must be one of: {valid_depths}")
    
    def _parse_response(self, response_content: str) -> Dict[str, Any]:
        """Parse analysis agent response.
        
        Args:
            response_content: Raw LLM response (expected to be JSON with analysis)
            
        Returns:
            Parsed analysis output
        """
        try:
            output = json.loads(response_content)
            
            # Validate analysis structure
            if "analysis" not in output:
                output["analysis"] = {}
            
            analysis = output["analysis"]
            
            # Ensure required fields exist
            required_fields = {
                "completeness_score": 0,
                "gaps_identified": [],
                "risks": [],
                "feasibility_assessment": "Unknown",
                "recommendations": [],
                "estimated_effort": "Unknown",
                "dependencies": [],
            }
            
            for field, default in required_fields.items():
                if field not in analysis:
                    analysis[field] = default
            
            # Flatten output for easier use
            output.update(analysis)
            
            return output
            
        except json.JSONDecodeError as e:
            logger.error("analysis_response_parse_failed", error=str(e))
            return {
                "completeness_score": 0,
                "gaps_identified": [],
                "risks": [],
                "feasibility_assessment": "Failed to analyze",
                "recommendations": [],
                "estimated_effort": "Unknown",
                "dependencies": [],
            }
