"""
Database models for conversations and messages.

This module defines SQLAlchemy ORM models for storing PM Agent chat history,
including conversations and individual messages.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


class MessageRole(enum.Enum):
    """Enumeration for message roles in a conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(Base):
    """
    Represents a conversation thread in the PM Agent chat system.
    
    Attributes:
        id: Unique identifier for the conversation
        title: Human-readable title for the conversation
        user_id: ID of the user who owns this conversation
        created_at: Timestamp when the conversation was created
        updated_at: Timestamp when the conversation was last updated
        messages: Relationship to associated Message objects
    """
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    user_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to messages
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title='{self.title}', user_id='{self.user_id}')>"


class Message(Base):
    """
    Represents an individual message within a conversation.
    
    Attributes:
        id: Unique identifier for the message
        conversation_id: Foreign key to the parent conversation
        role: Role of the message sender (user, assistant, or system)
        content: The actual message content
        created_at: Timestamp when the message was created
        conversation: Relationship to parent Conversation object
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role={self.role.value})>"
