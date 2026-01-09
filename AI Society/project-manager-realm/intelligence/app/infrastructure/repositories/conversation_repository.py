"""Repository interface for data access abstraction.

Defines the contract for data persistence operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class ConversationRepository(ABC):
    """Abstract repository for conversation persistence."""
    
    @abstractmethod
    async def create(
        self,
        conversation_id: str,
        workspace_id: str,
        slack_channel_id: str,
        thread_ts: str,
    ) -> None:
        """Create a new conversation."""
        pass
    
    @abstractmethod
    async def get_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation state."""
        pass
    
    @abstractmethod
    async def update_state(
        self,
        conversation_id: str,
        state: Dict[str, Any],
    ) -> None:
        """Update conversation state."""
        pass
    
    @abstractmethod
    async def get_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get conversation message history."""
        pass
    
    @abstractmethod
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> str:
        """Add message to conversation."""
        pass
