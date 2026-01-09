# intelligence/service/app/schemas/agent_schemas.py
"""Pydantic schemas for agent inputs and outputs."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Clarification Agent
# ============================================================================

class ClarificationInput(BaseModel):
    """Input schema for clarification agent."""
    
    user_description: str = Field(..., description="Initial requirement description")
    project_context: str = Field(..., description="Project context")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default_factory=list,
        description="Previous conversation exchanges"
    )


class ClarificationQuestion(BaseModel):
    """Individual clarifying question."""
    
    id: str
    text: str
    category: str
    priority: str


class ClarificationOutput(BaseModel):
    """Output schema for clarification agent."""
    
    questions: List[ClarificationQuestion]
    rationale: str
    estimated_confidence: float


# ============================================================================
# PRD Generator Agent
# ============================================================================

class PRDGeneratorInput(BaseModel):
    """Input schema for PRD generator agent."""
    
    requirement_description: str = Field(..., description="Clarified requirement")
    clarification_answers: List[Dict[str, str]] = Field(
        ...,
        description="Answers to clarification questions"
    )
    project_context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Project metadata"
    )


class PRDGeneratorOutput(BaseModel):
    """Output schema for PRD generator agent."""
    
    prd: Dict[str, Any] = Field(..., description="Complete PRD with 9 sections")
    completeness_score: float = Field(..., description="Completeness score 0-1")
    estimated_effort: str = Field(..., description="Estimated effort")


# ============================================================================
# Analysis Agent
# ============================================================================

class AnalysisInput(BaseModel):
    """Input schema for analysis agent."""
    
    requirements: Dict[str, Any] = Field(..., description="Requirements/PRD to analyze")
    analysis_depth: str = Field(
        default="standard",
        description="Analysis depth: quick, standard, or deep"
    )


class AnalysisOutput(BaseModel):
    """Output schema for analysis agent."""
    
    completeness_score: float = Field(..., description="Completeness score 0-100")
    gaps_identified: List[str] = Field(..., description="Identified gaps")
    risks: List[Dict[str, str]] = Field(..., description="Identified risks")
    feasibility_assessment: str
    recommendations: List[str]
    estimated_effort: str
    dependencies: List[str]


# ============================================================================
# Generic Agent Execution
# ============================================================================

class AgentExecutionRequest(BaseModel):
    """Generic agent execution request."""
    
    agent_name: str = Field(..., description="Name of the agent to execute")
    inputs: Dict[str, Any] = Field(..., description="Input parameters for the agent")


class AgentExecutionResponse(BaseModel):
    """Generic agent execution response."""
    
    agent: str = Field(..., description="Agent name")
    status: str = Field(..., description="Execution status (success/failure)")
    result: Dict[str, Any] = Field(..., description="Agent output")
    error: Optional[str] = Field(None, description="Error message if failed")
    duration_ms: Optional[int] = Field(None, description="Execution duration in milliseconds")
