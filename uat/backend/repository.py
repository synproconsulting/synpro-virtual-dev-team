"""Repository layer for conversations, messages, and products."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session

from models import Conversation, Message, MessageRole, Product


# ?? Conversation / Message repositories (SDT1-49) ????????????????????????????

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
        message = Message(conversation_id=conversation_id, role=MessageRole(role), content=content)
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


# ?? Product repository (SDT1-51) ??????????????????????????????????????????????

class ProductRepository:
    """Repository for product configuration database operations."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def create_product(
        self,
        name: str,
        jira_project_key: str,
        github_repo: str,
        railway_service_id: Optional[str] = None,
        sonarcloud_key: Optional[str] = None,
    ) -> Product:
        product = Product(
            name=name,
            jira_project_key=jira_project_key,
            github_repo=github_repo,
            railway_service_id=railway_service_id,
            sonarcloud_key=sonarcloud_key,
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def get_by_id(self, product_id: UUID) -> Optional[Product]:
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_by_name(self, name: str) -> Optional[Product]:
        return self.db.query(Product).filter(Product.name == name).first()

    def list_products(self, skip: int = 0, limit: int = 100) -> List[Product]:
        return self.db.query(Product).order_by(Product.name).offset(skip).limit(limit).all()

    def update_product(self, product_id: UUID, **kwargs) -> Optional[Product]:
        product = self.get_by_id(product_id)
        if product:
            for key, value in kwargs.items():
                if hasattr(product, key):
                    setattr(product, key, value)
            self.db.commit()
            self.db.refresh(product)
        return product

    def delete_product(self, product_id: UUID) -> bool:
        product = self.get_by_id(product_id)
        if product:
            self.db.delete(product)
            self.db.commit()
            return True
        return False

    def count_products(self) -> int:
        return self.db.query(Product).count()