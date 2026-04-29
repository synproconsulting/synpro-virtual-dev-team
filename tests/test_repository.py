"""
Unit tests for conversation and message repositories.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.chat.models import Base, Conversation, Message, MessageRole
from src.chat.repository import ConversationRepository, MessageRepository


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def conversation_repo(db_session):
    """Create a ConversationRepository instance."""
    return ConversationRepository(db_session)


@pytest.fixture
def message_repo(db_session):
    """Create a MessageRepository instance."""
    return MessageRepository(db_session)


class TestConversationRepository:
    """Tests for ConversationRepository."""

    def test_create_conversation(self, conversation_repo):
        """Test creating a conversation."""
        conversation = conversation_repo.create_conversation(
            title="My Conversation",
            user_id="user456"
        )

        assert conversation.id is not None
        assert conversation.title == "My Conversation"
        assert conversation.user_id == "user456"

    def test_get_conversation_by_id(self, conversation_repo):
        """Test retrieving a conversation by ID."""
        created = conversation_repo.create_conversation(
            title="Test",
            user_id="user123"
        )

        retrieved = conversation_repo.get_conversation_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Test"

    def test_get_conversation_by_id_not_found(self, conversation_repo):
        """Test retrieving a non-existent conversation."""
        result = conversation_repo.get_conversation_by_id(99999)
        assert result is None

    def test_get_user_conversations(self, conversation_repo):
        """Test retrieving all conversations for a user."""
        conversation_repo.create_conversation("Conv 1", "user1")
        conversation_repo.create_conversation("Conv 2", "user1")
        conversation_repo.create_conversation("Conv 3", "user2")

        user1_conversations = conversation_repo.get_user_conversations("user1")
        assert len(user1_conversations) == 2

        user2_conversations = conversation_repo.get_user_conversations("user2")
        assert len(user2_conversations) == 1

    def test_get_user_conversations_pagination(self, conversation_repo):
        """Test pagination of user conversations."""
        for i in range(5):
            conversation_repo.create_conversation(f"Conv {i}", "user1")

        page1 = conversation_repo.get_user_conversations("user1", skip=0, limit=2)
        assert len(page1) == 2

        page2 = conversation_repo.get_user_conversations("user1", skip=2, limit=2)
        assert len(page2) == 2

        page3 = conversation_repo.get_user_conversations("user1", skip=4, limit=2)
        assert len(page3) == 1

    def test_count_user_conversations(self, conversation_repo):
        """Test counting user conversations."""
        conversation_repo.create_conversation("Conv 1", "user1")
        conversation_repo.create_conversation("Conv 2", "user1")
        conversation_repo.create_conversation("Conv 3", "user2")

        count_user1 = conversation_repo.count_user_conversations("user1")
        assert count_user1 == 2

        count_user2 = conversation_repo.count_user_conversations("user2")
        assert count_user2 == 1

    def test_update_conversation(self, conversation_repo):
        """Test updating a conversation title."""
        conversation = conversation_repo.create_conversation(
            title="Old Title",
            user_id="user1"
        )

        updated = conversation_repo.update_conversation(
            conversation.id,
            "New Title"
        )

        assert updated is not None
        assert updated.title == "New Title"
        assert updated.id == conversation.id

    def test_update_conversation_not_found(self, conversation_repo):
        """Test updating a non-existent conversation."""
        result = conversation_repo.update_conversation(99999, "New Title")
        assert result is None

    def test_delete_conversation(self, conversation_repo):
        """Test deleting a conversation."""
        conversation = conversation_repo.create_conversation(
            title="To Delete",
            user_id="user1"
        )

        deleted = conversation_repo.delete_conversation(conversation.id)
        assert deleted is True

        # Verify it's gone
        retrieved = conversation_repo.get_conversation_by_id(conversation.id)
        assert retrieved is None

    def test_delete_conversation_not_found(self, conversation_repo):
        """Test deleting a non-existent conversation."""
        result = conversation_repo.delete_conversation(99999)
        assert result is False


class TestMessageRepository:
    """Tests for MessageRepository."""

    def test_create_message(self, conversation_repo, message_repo):
        """Test creating a message."""
        conversation = conversation_repo.create_conversation(
            title="Test",
            user_id="user1"
        )

        message = message_repo.create_message(
            conversation_id=conversation.id,
            role="user",
            content="Hello, world!"
        )

        assert message.id is not None
        assert message.conversation_id == conversation.id
        assert message.role == MessageRole.USER
        assert message.content == "Hello, world!"

    def test_get_conversation_messages(self, conversation_repo, message_repo):
        """Test retrieving all messages for a conversation."""
        conversation = conversation_repo.create_conversation(
            title="Test",
            user_id="user1"
        )

        message_repo.create_message(conversation.id, "user", "Message 1")
        message_repo.create_message(conversation.id, "assistant", "Message 2")
        message_repo.create_message(conversation.id, "user", "Message 3")

        messages = message_repo.get_conversation_messages(conversation.id)
        assert len(messages) == 3
        assert messages[0].content == "Message 1"
        assert messages[1].content == "Message 2"
        assert messages[2].content == "Message 3"

    def test_get_conversation_messages_pagination(self, conversation_repo, message_repo):
        """Test pagination of conversation messages."""
        conversation = conversation_repo.create_conversation(
            title="Test",
            user_id="user1"
        )

        for i in range(5):
            message_repo.create_message(conversation.id, "user", f"Message {i}")

        page1 = message_repo.get_conversation_messages(conversation.id, skip=0, limit=2)
        assert len(page1) == 2

        page2 = message_repo.get_conversation_messages(conversation.id, skip=2, limit=2)
        assert len(page2) == 2

    def test_get_message_by_id(self, conversation_repo, message_repo):
        """Test retrieving a message by ID."""
        conversation = conversation_repo.create_conversation(
            title="Test",
            user_id="user1"
        )

        created = message_repo.create_message(
            conversation.id,
            "user",
            "Test message"
        )

        retrieved = message_repo.get_message_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.content == "Test message"

    def test_get_message_by_id_not_found(self, message_repo):
        """Test retrieving a non-existent message."""
        result = message_repo.get_message_by_id(99999)
        assert result is None

    def test_delete_message(self, conversation_repo, message_repo):
        """Test deleting a message."""
        conversation = conversation_repo.create_conversation(
            title="Test",
            user_id="user1"
        )

        message = message_repo.create_message(
            conversation.id,
            "user",
            "To delete"
        )

        deleted = message_repo.delete_message(message.id)
        assert deleted is True

        # Verify it's gone
        retrieved = message_repo.get_message_by_id(message.id)
        assert retrieved is None

    def test_delete_message_not_found(self, message_repo):
        """Test deleting a non-existent message."""
        result = message_repo.delete_message(99999)
        assert result is False

    def test_create_message_updates_conversation_timestamp(
        self, 
        conversation_repo, 
        message_repo
    ):
        """Test that creating a message updates conversation's updated_at."""
        conversation = conversation_repo.create_conversation(
            title="Test",
            user_id="user1"
        )
        original_updated_at = conversation.updated_at

        import time
        time.sleep(0.01)  # Small delay to ensure different timestamp

        message_repo.create_message(
            conversation.id,
            "user",
            "New message"
        )

        # Refresh the conversation
        updated_conversation = conversation_repo.get_conversation_by_id(conversation.id)
        assert updated_conversation.updated_at >= original_updated_at
