"""PostgreSQL implementation of ConversationRepository."""

import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.models import (
    Conversation,
    Message,
)
from app.infrastructure.repositories.conversation_repository import (
    ConversationRepository,
)


class PostgresConversationRepository(ConversationRepository):
    """PostgreSQL implementation of conversation repository."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize with database session.
        
        Args:
            db_session: Async SQLAlchemy session
        """
        self.db_session = db_session
    
    async def create(
        self,
        conversation_id: str,
        workspace_id: str,
        slack_channel_id: str,
        thread_ts: str,
    ) -> None:
        """Create a new conversation."""
        conversation = Conversation(
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            slack_channel_id=slack_channel_id,
            thread_ts=thread_ts,
            state={},
            created_at=datetime.now(timezone.utc),
        )
        self.db_session.add(conversation)
        await self.db_session.flush()
    
    async def get_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation state."""
        query = select(Conversation.state).where(
            Conversation.conversation_id == conversation_id
        )
        result = await self.db_session.execute(query)
        state = result.scalar()
        return state if state else None
    
    async def update_state(
        self,
        conversation_id: str,
        state: Dict[str, Any],
    ) -> None:
        """Update conversation state."""
        stmt = (
            update(Conversation)
            .where(Conversation.conversation_id == conversation_id)
            .values(state=state, updated_at=datetime.now(timezone.utc))
        )
        await self.db_session.execute(stmt)
        await self.db_session.flush()
    
    async def get_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get conversation message history."""
        query = (
            select(Message.role, Message.content)
            .select_from(Message)
            .join(Conversation)
            .where(Conversation.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        result = await self.db_session.execute(query)
        rows = result.fetchall()
        return [
            {"role": row[0], "content": row[1]}
            for row in rows
        ]
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> str:
        """Add message to conversation and return message ID."""
        # Get conversation ID from conversation_id
        conv_query = select(Conversation.id).where(
            Conversation.conversation_id == conversation_id
        )
        conv_result = await self.db_session.execute(conv_query)
        conv_id = conv_result.scalar_one()
        
        message = Message(
            conversation_id=conv_id,
            role=role,
            content=content,
            created_at=datetime.now(timezone.utc),
        )
        self.db_session.add(message)
        await self.db_session.flush()
        return str(message.id)
