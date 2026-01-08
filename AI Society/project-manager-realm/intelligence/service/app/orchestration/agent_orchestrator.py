# intelligence/service/app/orchestration/agent_orchestrator.py
"""Agent orchestrator - Coordinates agent execution."""

from typing import Dict, Any, Optional
import structlog
import asyncio

from app.agents import (
    ClarificationAgent,
    PRDGeneratorAgent,
    AnalysisAgent,
)
from app.schemas import (
    ClarificationInput,
    ClarificationOutput,
    PRDGeneratorInput,
    PRDGeneratorOutput,
    AnalysisInput,
    AnalysisOutput,
)

logger = structlog.get_logger()


class AgentOrchestrator:
    """Orchestrates agent execution - selects and runs appropriate agents."""
    
    def __init__(self):
        """Initialize agent orchestrator."""
        self.clarification_agent = ClarificationAgent()
        self.prd_generator_agent = PRDGeneratorAgent()
        self.analysis_agent = AnalysisAgent()
        
        logger.info("agent_orchestrator_initialized")
    
    async def execute_clarification_agent(
        self,
        user_description: str,
        project_context: str,
        conversation_history: Optional[list] = None,
    ) -> ClarificationOutput:
        """Execute clarification agent.
        
        Args:
            user_description: Initial requirement description
            project_context: Project context
            conversation_history: Previous conversation
            
        Returns:
            Clarification output
        """
        logger.info("executing_clarification_agent")
        
        inputs = {
            "user_description": user_description,
            "project_context": project_context,
            "conversation_history": conversation_history or [],
        }
        
        result = await self.clarification_agent.execute(inputs)
        return ClarificationOutput(**result)
    
    async def execute_prd_generator_agent(
        self,
        requirement_description: str,
        clarification_answers: list,
        project_context: Optional[Dict[str, Any]] = None,
    ) -> PRDGeneratorOutput:
        """Execute PRD generator agent.
        
        Args:
            requirement_description: Clarified requirement
            clarification_answers: Answers to clarification questions
            project_context: Project metadata
            
        Returns:
            PRD output
        """
        logger.info("executing_prd_generator_agent")
        
        inputs = {
            "requirement_description": requirement_description,
            "clarification_answers": clarification_answers,
            "project_context": project_context or {},
        }
        
        result = await self.prd_generator_agent.execute(inputs)
        return PRDGeneratorOutput(**result)
    
    async def execute_analysis_agent(
        self,
        requirements: Dict[str, Any],
        analysis_depth: str = "standard",
    ) -> AnalysisOutput:
        """Execute analysis agent.
        
        Args:
            requirements: Requirements/PRD to analyze
            analysis_depth: Analysis depth (quick, standard, deep)
            
        Returns:
            Analysis output
        """
        logger.info("executing_analysis_agent", depth=analysis_depth)
        
        inputs = {
            "requirements": requirements,
            "analysis_depth": analysis_depth,
        }
        
        result = await self.analysis_agent.execute(inputs)
        return AnalysisOutput(**result)
    
    async def execute_full_workflow(
        self,
        user_description: str,
        project_context: str,
    ) -> Dict[str, Any]:
        """Execute full requirement-to-PRD-to-analysis workflow.
        
        Args:
            user_description: Initial requirement
            project_context: Project context
            
        Returns:
            Complete workflow results
        """
        logger.info("executing_full_workflow")
        
        try:
            # Step 1: Clarification
            clarification_result = await self.execute_clarification_agent(
                user_description=user_description,
                project_context=project_context,
            )
            logger.info("clarification_step_complete")
            
            # Step 2: PRD Generation (using clarification as context)
            prd_result = await self.execute_prd_generator_agent(
                requirement_description=user_description,
                clarification_answers=[
                    {"q_id": q.id, "answer": q.text}
                    for q in clarification_result.questions
                ],
                project_context={"source": "workflow"},
            )
            logger.info("prd_generation_step_complete")
            
            # Step 3: Analysis (in parallel with other work if needed)
            analysis_result = await self.execute_analysis_agent(
                requirements=prd_result.prd,
                analysis_depth="standard",
            )
            logger.info("analysis_step_complete")
            
            return {
                "clarification": clarification_result.dict(),
                "prd": prd_result.dict(),
                "analysis": analysis_result.dict(),
            }
            
        except Exception as e:
            logger.error("full_workflow_failed", error=str(e))
            raise


# Global agent orchestrator instance
_agent_orchestrator: Optional[AgentOrchestrator] = None


def get_agent_orchestrator() -> AgentOrchestrator:
    """Get or create global agent orchestrator instance.
    
    Returns:
        AgentOrchestrator instance
    """
    global _agent_orchestrator
    
    if _agent_orchestrator is None:
        _agent_orchestrator = AgentOrchestrator()
    
    return _agent_orchestrator
