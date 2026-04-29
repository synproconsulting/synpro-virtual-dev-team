"""
Unit tests for conversation and message models.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.chat.models import Base, Conversation, Message, MessageRole


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


class TestConversationModel:
    """Tests for the Conversation model."""

    def test_create_conversation(self, db_session):
        """Test creating a conversation."""
        conversation = Conversation(
            title="Test Conversation",
            user_id="user123"
        )
        db_session.add(conversation)
        db_session.commit()

        assert conversation.id is not None
        assert conversation.title == "Test Conversation"
        assert conversation.user_id == "user123"
        assert isinstance(conversation.created_at, datetime)
        assert isinstance(conversation.updated_at, datetime)

    def test_conversation_repr(self, db_session):
        """Test conversation string representation."""
        conversation = Conversation(
            title="Test Conversation",
            user_id="user123"
        )
        db_session.add(conversation)
        db_session.commit()

        repr_str = repr(conversation)
        assert "Conversation" in repr_str
        assert "Test Conversation" in repr_str
        assert "user123" in repr_str

    def test_conversation_messages_relationship(self, db_session):
        """Test the relationship between conversation and messages."""
        conversation = Conversation(
            title="Test Conversation",
            user_id="user123"
        )
        db_session.add(conversation)
        db_session.commit()

        message1 = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="Hello"
        )
        message2 = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content="Hi there!"
        )
        db_session.add_all([message1, message2])
        db_session.commit()

        assert len(conversation.messages) == 2
        assert conversation.messages[0].content == "Hello"
        assert conversation.messages[1].content == "Hi there!"

    def test_conversation_cascade_delete(self, db_session):
        """Test that deleting a conversation deletes its messages."""
        conversation = Conversation(
            title="Test Conversation",
            user_id="user123"
        )
        db_session.add(conversation)
        db_session.commit()

        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="Hello"
        )
        db_session.add(message)
        db_session.commit()

        conversation_id = conversation.id
        db_session.delete(conversation)
        db_session.commit()

        # Verify messages are also deleted
        remaining_messages = db_session.query(Message).filter(
            Message.conversation_id == conversation_id
        ).all()
        assert len(remaining_messages) == 0


class TestMessageModel:
    """Tests for the Message model."""

    def test_create_message(self, db_session):
        """Test creating a message."""
        conversation = Conversation(
            title="Test Conversation",
            user_id="user123"
        )
        db_session.add(conversation)
        db_session.commit()

        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="Hello, world!"
        )
        db_session.add(message)
        db_session.commit()

        assert message.id is not None
        assert message.conversation_id == conversation.id
        assert message.role == MessageRole.USER
        assert message.content == "Hello, world!"
        assert isinstance(message.created_at, datetime)

    def test_message_repr(self, db_session):
        """Test message string representation."""
        conversation = Conversation(
            title="Test Conversation",
            user_id="user123"
        )
        db_session.add(conversation)
        db_session.commit()

        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content="Test message"
        )
        db_session.add(message)
        db_session.commit()

        repr_str = repr(message)
        assert "Message" in repr_str
        assert "assistant" in repr_str

    def test_message_roles(self, db_session):
        """Test different message roles."""
        conversation = Conversation(
            title="Test Conversation",
            user_id="user123"
        )
        db_session.add(conversation)
        db_session.commit()

        user_msg = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="User message"
        )
        assistant_msg = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content="Assistant message"
        )
        system_msg = Message(
            conversation_id=conversation.id,
            role=MessageRole.SYSTEM,
            content="System message"
        )

        db_session.add_all([user_msg, assistant_msg, system_msg])
        db_session.commit()

        assert user_msg.role == MessageRole.USER
        assert assistant_msg.role == MessageRole.ASSISTANT
        assert system_msg.role == MessageRole.SYSTEM

    def test_message_conversation_relationship(self, db_session):
        """Test the relationship from message to conversation."""
        conversation = Conversation(
            title="Test Conversation",
            user_id="user123"
        )
        db_session.add(conversation)
        db_session.commit()

        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="Hello"
        )
        db_session.add(message)
        db_session.commit()

        assert message.conversation.id == conversation.id
        assert message.conversation.title == "Test Conversation"
