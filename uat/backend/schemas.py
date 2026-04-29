"""Pydantic schemas for conversations, messages, and products."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# ?? Conversation / Message schemas (SDT1-49) ??????????????????????????????????

class MessageBase(BaseModel):
    role: str = Field(..., description="Role of the message sender (user, assistant, or system)")
    content: str = Field(..., min_length=1)


class MessageCreate(MessageBase):
    conversation_id: int = Field(..., gt=0)


class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConversationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class ConversationCreate(ConversationBase):
    user_id: str = Field(..., min_length=1, max_length=100)


class ConversationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)


class ConversationResponse(ConversationBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConversationWithMessages(ConversationResponse):
    messages: List[MessageResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)


# ?? Product schemas (SDT1-51) ?????????????????????????????????????????????????

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Unique product identifier")
    jira_project_key: str = Field(..., min_length=1, max_length=50, description="Jira project key, e.g. SDT1")
    github_repo: str = Field(..., min_length=1, max_length=255, description="GitHub repo slug, e.g. org/repo")
    railway_service_id: Optional[str] = Field(None, max_length=255)
    sonarcloud_key: Optional[str] = Field(None, max_length=255)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    jira_project_key: Optional[str] = Field(None, min_length=1, max_length=50)
    github_repo: Optional[str] = Field(None, min_length=1, max_length=255)
    railway_service_id: Optional[str] = None
    sonarcloud_key: Optional[str] = None


class ProductResponse(ProductBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)