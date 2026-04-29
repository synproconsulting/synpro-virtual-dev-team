"""Repository layer for conversations and messages."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models import Conversation, Message, MessageRole


class ConversationRepository:
    """Repository for conversation database operations."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def create_conversation(self, title: str, user_id: str) -> Conversation:
        conversation = Conversation(title=title, user_id=user_id)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_conversation_by_id(self, conversation_id: int) -> Optional[Conversation]:
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def get_user_conversations(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Conversation]:
        return (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_user_conversations(self, user_id: str) -> int:
        return self.db.query(Conversation).filter(Conversation.user_id == user_id).count()

    def update_conversation(self, conversation_id: int, title: str) -> Optional[Conversation]:
        conversation = self.get_conversation_by_id(conversation_id)
        if conversation:
            conversation.title = title
            conversation.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(conversation)
        return conversation

    def delete_conversation(self, conversation_id: int) -> bool:
        conversation = self.get_conversation_by_id(conversation_id)
        if conversation:
            self.db.delete(conversation)
            self.db.commit()
            return True
        return False


class MessageRepository:
    """Repository for message database operations."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def create_message(self, conversation_id: int, role: str, content: str) -> Message:
        message_role = MessageRole(role)
        message = Message(conversation_id=conversation_id, role=message_role, content=content)
        self.db.add(message)
        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_conversation_messages(self, conversation_id: int, skip: int = 0, limit: int = 100) -> List[Message]:
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_message_by_id(self, message_id: int) -> Optional[Message]:
        return self.db.query(Message).filter(Message.id == message_id).first()

    def delete_message(self, message_id: int) -> bool:
        message = self.get_message_by_id(message_id)
        if message:
            self.db.delete(message)
            self.db.commit()
            return True
        return False