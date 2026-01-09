"""SQLAlchemy ORM models for infrastructure layer."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def _utc_now():
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class Conversation(Base):
    """Conversation table model."""
    
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(String(255), unique=True, nullable=False, index=True)
    workspace_id = Column(String(255), nullable=False)
    slack_channel_id = Column(String(255), nullable=False)
    thread_ts = Column(String(50), nullable=False)
    state = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=_utc_now, nullable=False)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, conversation_id={self.conversation_id})>"


class Message(Base):
    """Message table model."""
    
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # "user" or "assistant"
    content = Column(String(4096), nullable=False)
    created_at = Column(DateTime, default=_utc_now, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role={self.role})>"
