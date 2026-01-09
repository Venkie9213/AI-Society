"""Agent execution wrapper with consistent interface.

Handles agent orchestration and output serialization.
"""

from typing import Any, Dict, Optional, List

import structlog

logger = structlog.get_logger()


class AgentOutput:
    """Wrapper for agent output with normalized interface."""
    
    def __init__(self, output: Any):
        self.output = output
    
    def get_questions(self) -> List[Dict[str, Any]]:
        """Extract questions from agent output."""
        questions = []
        if hasattr(self.output, 'questions') and self.output.questions:
            for q in self.output.questions:
                if hasattr(q, 'dict'):
                    questions.append(q.dict())
                elif hasattr(q, '__dict__'):
                    questions.append(vars(q))
                else:
                    questions.append({"text": str(q), "category": "", "priority": ""})
        return questions
    
    def get_rationale(self) -> str:
        """Extract rationale from agent output."""
        if hasattr(self.output, 'rationale'):
            return self.output.rationale
        return ""
    
    def get_confidence(self) -> float:
        """Extract confidence score from agent output."""
        if hasattr(self.output, 'estimated_confidence'):
            return float(self.output.estimated_confidence * 100)
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert output to dictionary for storage."""
        try:
            if hasattr(self.output, 'dict'):
                return self.output.dict()
            else:
                return vars(self.output) if hasattr(self.output, '__dict__') else {}
        except Exception as e:
            logger.warning("agent_output_conversion_failed", error=str(e))
            return {"content": str(self.output)}


class AgentRunner:
    """Executes agents with consistent interface and error handling.
    
    Single Responsibility: Execute agents and normalize output.
    """
    
    def __init__(self, orchestrator: Any):  # AgentOrchestrator
        self.orchestrator = orchestrator
    
    async def run_clarification_agent(
        self,
        user_text: str,
        conversation_history: List[Dict[str, str]],
    ) -> Optional[AgentOutput]:
        """Run clarification agent and normalize output."""
        try:
            logger.info("agent_execution_starting", agent="clarification")
            
            output = await self.orchestrator.execute_clarification_agent(
                user_text=user_text,
                conversation_history=conversation_history,
            )
            
            logger.info("agent_execution_completed", agent="clarification")
            return AgentOutput(output)
        except Exception as e:
            logger.error("agent_execution_failed", agent="clarification", error=str(e))
            raise
