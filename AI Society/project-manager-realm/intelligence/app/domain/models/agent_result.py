"""Domain models for agent results.

Represents the output of agent execution in domain terms.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ClarificationQuestion:
    """Represents a single clarification question."""
    text: str
    category: str
    priority: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "category": self.category,
            "priority": self.priority,
        }


@dataclass
class AgentExecutionResult:
    """Result of agent execution with normalized interface."""
    
    success: bool
    agent_name: str
    confidence_score: float
    questions: List[Dict[str, Any]] = field(default_factory=list)
    rationale: str = ""
    raw_output: Optional[Any] = None
    error: Optional[str] = None
    
    @property
    def is_confident(self) -> bool:
        """Check if result is confident."""
        return self.confidence_score >= 95.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "success": self.success,
            "agent_name": self.agent_name,
            "confidence_score": self.confidence_score,
            "questions": self.questions,
            "rationale": self.rationale,
            "is_confident": self.is_confident,
        }
