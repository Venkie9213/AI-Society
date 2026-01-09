"""Conversation management and state tracking.

Handles conversation creation, state retrieval, and updates using the repository pattern.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text as sql_text

import structlog

logger = structlog.get_logger()


class ConversationState:
    """Value object representing conversation state."""
    
    def __init__(
        self,
        conversation_id: str,
        current_agent: str,
        confidence_score: float,
        turns_count: int,
        metadata: Dict[str, Any],
    ):
        self.conversation_id = conversation_id
        self.current_agent = current_agent
        self.confidence_score = confidence_score
        self.turns_count = turns_count
        self.metadata = metadata

    def is_confident(self, threshold: float = 95.0) -> bool:
        """Check if conversation has reached confidence threshold."""
        return self.confidence_score >= threshold


class ConversationManager:
    """Manages conversation lifecycle and state persistence.
    
    Uses repository pattern to abstract database operations.
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def get_or_create_conversation(
        self,
        conversation_id: str,
        workspace_id: str,
        slack_channel_id: str,
        thread_ts: str,
    ) -> None:
        """Get or create a conversation."""
        try:
            await self.db_session.execute(
                sql_text("""
                    INSERT INTO conversations 
                    (conversation_id, workspace_id, channel_id, thread_ts, created_at)
                    VALUES (:conversation_id, :workspace_id, :channel_id, :thread_ts, :created_at)
                    ON CONFLICT (conversation_id) DO NOTHING
                """),
                {
                    "conversation_id": conversation_id,
                    "workspace_id": workspace_id,
                    "channel_id": slack_channel_id,
                    "thread_ts": thread_ts,
                    "created_at": datetime.now(timezone.utc),
                }
            )
            await self.db_session.commit()
        except Exception as e:
            logger.warning("conversation_creation_failed", error=str(e))
            await self.db_session.rollback()
    
    async def get_state(self, conversation_id: str) -> Optional[ConversationState]:
        """Retrieve conversation state from database."""
        try:
            result = await self.db_session.execute(
                sql_text("""
                    SELECT current_agent, confidence_score, turns_count, metadata
                    FROM conversation_states
                    WHERE conversation_id = :conversation_id
                """),
                {"conversation_id": conversation_id}
            )
            
            row = result.first()
            if row:
                metadata = row[3] or {}
                if isinstance(metadata, str):
                    metadata = json.loads(metadata)
                
                return ConversationState(
                    conversation_id=conversation_id,
                    current_agent=row[0],
                    confidence_score=float(row[1]),
                    turns_count=row[2],
                    metadata=metadata,
                )
            return None
        except Exception as e:
            logger.error("conversation_state_retrieval_failed", error=str(e))
            raise
    
    async def update_state(
        self,
        conversation_id: str,
        current_agent: str,
        confidence_score: float,
        turns_count: int,
        metadata: Dict[str, Any],
    ) -> None:
        """Update or create conversation state."""
        try:
            existing_state = await self.get_state(conversation_id)
            
            if existing_state:
                await self.db_session.execute(
                    sql_text("""
                        UPDATE conversation_states
                        SET current_agent = :agent, confidence_score = :score,
                            turns_count = :turns, metadata = :metadata, updated_at = :updated_at
                        WHERE conversation_id = :conversation_id
                    """),
                    {
                        "agent": current_agent,
                        "score": confidence_score,
                        "turns": turns_count,
                        "metadata": json.dumps(metadata),
                        "conversation_id": conversation_id,
                        "updated_at": datetime.now(timezone.utc),
                    }
                )
            else:
                await self.db_session.execute(
                    sql_text("""
                        INSERT INTO conversation_states
                        (conversation_id, current_agent, confidence_score, turns_count, metadata, created_at)
                        VALUES (:conversation_id, :agent, :score, :turns, :metadata, :created_at)
                    """),
                    {
                        "conversation_id": conversation_id,
                        "agent": current_agent,
                        "score": confidence_score,
                        "turns": turns_count,
                        "metadata": json.dumps(metadata),
                        "created_at": datetime.now(timezone.utc),
                    }
                )
            
            await self.db_session.commit()
        except Exception as e:
            logger.error("conversation_state_update_failed", error=str(e))
            await self.db_session.rollback()
            raise
    
    async def get_conversation_history(
        self,
        conversation_id: str,
    ) -> List[Dict[str, str]]:
        """Get all messages in a conversation."""
        try:
            result = await self.db_session.execute(
                sql_text("""
                    SELECT role, content FROM messages
                    WHERE conversation_id = :conversation_id
                    ORDER BY created_at ASC
                """),
                {"conversation_id": conversation_id}
            )
            
            return [
                {"role": row[0], "content": row[1]}
                for row in result.fetchall()
            ]
        except Exception as e:
            logger.error("conversation_history_retrieval_failed", error=str(e))
            raise
    
    async def store_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> str:
        """Store a message in the conversation."""
        try:
            message_id = str(uuid.uuid4())
            await self.db_session.execute(
                sql_text("""
                    INSERT INTO messages
                    (message_id, conversation_id, role, content, created_at)
                    VALUES (:message_id, :conversation_id, :role, :content, :created_at)
                """),
                {
                    "message_id": message_id,
                    "conversation_id": conversation_id,
                    "role": role,
                    "content": content,
                    "created_at": datetime.now(timezone.utc),
                }
            )
            await self.db_session.commit()
            return message_id
        except Exception as e:
            logger.error("message_storage_failed", error=str(e))
            await self.db_session.rollback()
            raise
