# intelligence/service/app/schemas/__init__.py
"""Schemas module - Pydantic models for agent inputs/outputs and API DTOs."""

from app.schemas.agent_schemas import (
    ClarificationInput,
    ClarificationOutput,
    PRDGeneratorInput,
    PRDGeneratorOutput,
    AnalysisInput,
    AnalysisOutput,
    AgentExecutionRequest,
    AgentExecutionResponse,
)

# Import DTOs for API layer
from app.schemas.dtos import (
    AgentExecutionRequest as APIAgentExecutionRequest,
    AgentExecutionResponse as APIAgentExecutionResponse,
    ClarificationQuestion,
    PRDGeneratorRequest,
    AnalysisRequest,
    HealthCheckResponse,
    ErrorResponse,
)

__all__ = [
    # Agent schemas (business logic)
    "ClarificationInput",
    "ClarificationOutput",
    "PRDGeneratorInput",
    "PRDGeneratorOutput",
    "AnalysisInput",
    "AnalysisOutput",
    "AgentExecutionRequest",
    "AgentExecutionResponse",
    # DTOs (API layer)
    "APIAgentExecutionRequest",
    "APIAgentExecutionResponse",
    "ClarificationQuestion",
    "PRDGeneratorRequest",
    "AnalysisRequest",
    "HealthCheckResponse",
    "ErrorResponse",
]
