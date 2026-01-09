"""Agent API request/response DTOs.

Data transfer objects for agent execution endpoints.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


def _utc_now():
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class AgentExecutionRequest(BaseModel):
    """Base request for agent execution."""
    
    conversation_id: str = Field(..., description="Unique conversation identifier")
    user_description: str = Field(..., description="User's requirement description")
    project_context: Optional[str] = Field(None, description="Additional project context")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Previous messages in conversation",
    )


class ClarificationQuestion(BaseModel):
    """Single clarification question."""
    
    text: str = Field(..., description="Question text")
    category: Optional[str] = Field(None, description="Question category")
    priority: int = Field(default=1, description="Priority level (1-5)")


class AgentExecutionResponse(BaseModel):
    """Response from agent execution."""
    
    conversation_id: str = Field(..., description="Conversation identifier")
    agent: str = Field(..., description="Agent name")
    success: bool = Field(..., description="Whether execution succeeded")
    confidence_score: Optional[float] = Field(
        None,
        description="Confidence score (0-100) for next action",
        ge=0,
        le=100,
    )
    questions: Optional[List[ClarificationQuestion]] = Field(
        None,
        description="Clarification questions (if applicable)",
    )
    rationale: Optional[str] = Field(None, description="Rationale for agent decision")
    duration_ms: int = Field(..., description="Execution duration in milliseconds")
    timestamp: datetime = Field(default_factory=_utc_now)
    error: Optional[str] = Field(None, description="Error message if failed")


class PRDGeneratorRequest(AgentExecutionRequest):
    """Request for PRD generator agent."""
    
    pass


class AnalysisRequest(AgentExecutionRequest):
    """Request for analysis agent."""
    
    pass


class HealthCheckResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Health status (healthy/unhealthy)")
    timestamp: datetime = Field(default_factory=_utc_now)
    services: Dict[str, str] = Field(..., description="Status of each service")


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    timestamp: datetime = Field(default_factory=_utc_now)
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
