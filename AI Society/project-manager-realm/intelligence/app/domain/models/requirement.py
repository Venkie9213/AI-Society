"""Domain models for conversation entity.

Represents the core conversation business logic and validation.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class ConversationId:
    """Value object for conversation identity."""
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("ConversationId cannot be empty")


@dataclass
class SlackChannelRef:
    """Value object for Slack channel reference."""
    channel_id: str
    thread_ts: str
    
    @property
    def is_thread_reply(self) -> bool:
        """Check if this is a thread reply."""
        return bool(self.thread_ts)


@dataclass
class UserMessage:
    """Value object for user message."""
    text: str
    user_id: str
    timestamp: datetime
    
    @property
    def is_empty(self) -> bool:
        return not self.text or not self.text.strip()


@dataclass
class Requirement:
    """Core domain model for requirement."""
    conversation_id: ConversationId
    slack_ref: SlackChannelRef
    user_message: UserMessage
    confidence_score: float = 0.0
    is_complete: bool = False
    clarification_questions: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.clarification_questions is None:
            self.clarification_questions = []
        if self.metadata is None:
            self.metadata = {}
    
    def is_confident(self, threshold: float = 95.0) -> bool:
        """Check if requirement meets confidence threshold."""
        return self.confidence_score >= threshold
    
    def mark_complete(self, questions: List[Dict[str, Any]]):
        """Mark requirement as complete with final clarification."""
        self.is_complete = True
        self.clarification_questions = questions
    
    def add_clarification(self, questions: List[Dict[str, Any]]):
        """Add clarification questions for next round."""
        self.clarification_questions = questions
