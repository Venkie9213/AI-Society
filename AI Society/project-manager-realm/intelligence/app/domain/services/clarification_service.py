"""Clarification service - domain logic for clarification.

Handles clarification workflow and decision logic.
"""

from typing import List, Dict, Any
import structlog

from app.domain.models import AgentExecutionResult, Requirement

logger = structlog.get_logger()


class ClarificationService:
    """Handles clarification business logic.
    
    Single Responsibility: Clarification workflow decisions and transformations.
    """
    
    CONFIDENCE_THRESHOLD = 95.0
    
    @staticmethod
    def should_ask_more_questions(confidence_score: float) -> bool:
        """Determine if more clarification is needed."""
        return confidence_score < ClarificationService.CONFIDENCE_THRESHOLD
    
    @staticmethod
    def should_move_to_completion(confidence_score: float) -> bool:
        """Determine if requirements are sufficiently clear."""
        return confidence_score >= ClarificationService.CONFIDENCE_THRESHOLD
    
    @staticmethod
    def extract_questions(agent_result: AgentExecutionResult) -> List[Dict[str, Any]]:
        """Extract and validate questions from agent result."""
        if not agent_result.success:
            logger.warning("agent_result_not_successful", agent=agent_result.agent_name)
            return []
        
        questions = agent_result.questions or []
        
        # Validate questions format
        for q in questions:
            if not isinstance(q, dict):
                logger.warning("invalid_question_format", question=str(q))
                continue
            if "text" not in q:
                logger.warning("question_missing_text", question=q)
                continue
        
        return questions
    
    @staticmethod
    def build_metadata(
        agent_result: AgentExecutionResult,
        questions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build metadata from agent result."""
        return {
            "questions": questions,
            "rationale": agent_result.rationale,
            "agent": agent_result.agent_name,
        }
    
    @staticmethod
    def apply_result_to_requirement(
        requirement: Requirement,
        agent_result: AgentExecutionResult,
    ) -> None:
        """Apply agent result to requirement."""
        requirement.confidence_score = agent_result.confidence_score
        
        questions = ClarificationService.extract_questions(agent_result)
        
        if ClarificationService.should_move_to_completion(agent_result.confidence_score):
            requirement.mark_complete(questions)
            logger.info(
                "requirement_marked_complete",
                confidence=agent_result.confidence_score,
            )
        else:
            requirement.add_clarification(questions)
            logger.info(
                "requirement_needs_more_clarification",
                confidence=agent_result.confidence_score,
            )
