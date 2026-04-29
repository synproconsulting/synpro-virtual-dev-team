"""
Pydantic schemas for conversations and messages.

This module defines validation schemas for API requests and responses
related to conversations and messages in the PM Agent chat system.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class MessageRole:
    """Constants for message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageBase(BaseModel):
    """Base schema for message data."""
    role: str = Field(..., description="Role of the message sender (user, assistant, or system)")
    content: str = Field(..., min_length=1, description="Content of the message")


class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    conversation_id: int = Field(..., gt=0, description="ID of the conversation this message belongs to")


class MessageResponse(MessageBase):
    """Schema for message responses."""
    id: int = Field(..., description="Unique identifier for the message")
    conversation_id: int = Field(..., description="ID of the parent conversation")
    created_at: datetime = Field(..., description="Timestamp when the message was created")

    model_config = ConfigDict(from_attributes=True)


class ConversationBase(BaseModel):
    """Base schema for conversation data."""
    title: str = Field(..., min_length=1, max_length=255, description="Title of the conversation")


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""
    user_id: str = Field(..., min_length=1, max_length=100, description="ID of the user creating the conversation")


class ConversationUpdate(BaseModel):
    """Schema for updating an existing conversation."""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated title for the conversation")


class ConversationResponse(ConversationBase):
    """Schema for conversation responses without messages."""
    id: int = Field(..., description="Unique identifier for the conversation")
    user_id: str = Field(..., description="ID of the user who owns this conversation")
    created_at: datetime = Field(..., description="Timestamp when the conversation was created")
    updated_at: datetime = Field(..., description="Timestamp when the conversation was last updated")

    model_config = ConfigDict(from_attributes=True)


class ConversationWithMessages(ConversationResponse):
    """Schema for conversation responses including all messages."""
    messages: List[MessageResponse] = Field(default_factory=list, description="List of messages in the conversation")

    model_config = ConfigDict(from_attributes=True)


class ConversationListResponse(BaseModel):
    """Schema for paginated conversation list responses."""
    conversations: List[ConversationResponse] = Field(..., description="List of conversations")
    total: int = Field(..., ge=0, description="Total number of conversations")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Number of items per page")
