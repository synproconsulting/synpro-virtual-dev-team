"""
Repository layer for conversations and messages.

This module provides database access methods for managing conversations
and messages in the PM Agent chat system.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .models import Conversation, Message, MessageRole


class ConversationRepository:
    """Repository for conversation database operations."""

    def __init__(self, db_session: Session):
        """
        Initialize the repository with a database session.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session

    def create_conversation(self, title: str, user_id: str) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            title: Title for the conversation
            user_id: ID of the user creating the conversation
            
        Returns:
            Created Conversation object
        """
        conversation = Conversation(title=title, user_id=user_id)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_conversation_by_id(self, conversation_id: int) -> Optional[Conversation]:
        """
        Retrieve a conversation by its ID.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Conversation object if found, None otherwise
        """
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def get_user_conversations(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Conversation]:
        """
        Retrieve all conversations for a specific user.
        
        Args:
            user_id: ID of the user
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of Conversation objects
        """
        return (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_user_conversations(self, user_id: str) -> int:
        """
        Count total conversations for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Total count of conversations
        """
        return self.db.query(Conversation).filter(Conversation.user_id == user_id).count()

    def update_conversation(self, conversation_id: int, title: str) -> Optional[Conversation]:
        """
        Update a conversation's title.
        
        Args:
            conversation_id: ID of the conversation to update
            title: New title for the conversation
            
        Returns:
            Updated Conversation object if found, None otherwise
        """
        conversation = self.get_conversation_by_id(conversation_id)
        if conversation:
            conversation.title = title
            conversation.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(conversation)
        return conversation

    def delete_conversation(self, conversation_id: int) -> bool:
        """
        Delete a conversation and all its messages.
        
        Args:
            conversation_id: ID of the conversation to delete
            
        Returns:
            True if deleted, False if not found
        """
        conversation = self.get_conversation_by_id(conversation_id)
        if conversation:
            self.db.delete(conversation)
            self.db.commit()
            return True
        return False


class MessageRepository:
    """Repository for message database operations."""

    def __init__(self, db_session: Session):
        """
        Initialize the repository with a database session.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session

    def create_message(
        self, 
        conversation_id: int, 
        role: str, 
        content: str
    ) -> Message:
        """
        Create a new message in a conversation.
        
        Args:
            conversation_id: ID of the parent conversation
            role: Role of the message sender (user, assistant, system)
            content: Content of the message
            
        Returns:
            Created Message object
        """
        message_role = MessageRole(role)
        message = Message(
            conversation_id=conversation_id,
            role=message_role,
            content=content
        )
        self.db.add(message)
        
        # Update conversation's updated_at timestamp
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        if conversation:
            conversation.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_conversation_messages(
        self, 
        conversation_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Message]:
        """
        Retrieve all messages for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Message objects ordered by creation time
        """
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_message_by_id(self, message_id: int) -> Optional[Message]:
        """
        Retrieve a message by its ID.
        
        Args:
            message_id: ID of the message
            
        Returns:
            Message object if found, None otherwise
        """
        return self.db.query(Message).filter(Message.id == message_id).first()

    def delete_message(self, message_id: int) -> bool:
        """
        Delete a specific message.
        
        Args:
            message_id: ID of the message to delete
            
        Returns:
            True if deleted, False if not found
        """
        message = self.get_message_by_id(message_id)
        if message:
            self.db.delete(message)
            self.db.commit()
            return True
        return False
