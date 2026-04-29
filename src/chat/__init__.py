"""
Chat module for PM Agent conversation and message management.

This module provides database models, schemas, and repositories for managing
chat conversations and messages.
"""

from .models import Conversation, Message, MessageRole, Base
from .schemas import (
    MessageBase,
    MessageCreate,
    MessageResponse,
    ConversationBase,
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationWithMessages,
    ConversationListResponse,
)
from .repository import ConversationRepository, MessageRepository
from .database import (
    create_database_engine,
    create_tables,
    get_session_factory,
    get_db_session,
)

__all__ = [
    # Models
    "Conversation",
    "Message",
    "MessageRole",
    "Base",
    # Schemas
    "MessageBase",
    "MessageCreate",
    "MessageResponse",
    "ConversationBase",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "ConversationWithMessages",
    "ConversationListResponse",
    # Repositories
    "ConversationRepository",
    "MessageRepository",
    # Database
    "create_database_engine",
    "create_tables",
    "get_session_factory",
    "get_db_session",
]
