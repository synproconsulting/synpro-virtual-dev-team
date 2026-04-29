"""Unit tests for conversation and message repositories."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, MessageRole
from repository import ConversationRepository, MessageRepository


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def conversation_repo(db_session):
    return ConversationRepository(db_session)


@pytest.fixture
def message_repo(db_session):
    return MessageRepository(db_session)


class TestConversationRepository:

    def test_create_conversation(self, conversation_repo):
        conversation = conversation_repo.create_conversation(title="My Conversation", user_id="user456")
        assert conversation.id is not None
        assert conversation.title == "My Conversation"
        assert conversation.user_id == "user456"

    def test_get_conversation_by_id(self, conversation_repo):
        created = conversation_repo.create_conversation(title="Test", user_id="user123")
        retrieved = conversation_repo.get_conversation_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_conversation_by_id_not_found(self, conversation_repo):
        assert conversation_repo.get_conversation_by_id(99999) is None

    def test_get_user_conversations(self, conversation_repo):
        conversation_repo.create_conversation("Conv 1", "user1")
        conversation_repo.create_conversation("Conv 2", "user1")
        conversation_repo.create_conversation("Conv 3", "user2")
        assert len(conversation_repo.get_user_conversations("user1")) == 2
        assert len(conversation_repo.get_user_conversations("user2")) == 1

    def test_get_user_conversations_pagination(self, conversation_repo):
        for i in range(5):
            conversation_repo.create_conversation(f"Conv {i}", "user1")
        assert len(conversation_repo.get_user_conversations("user1", skip=0, limit=2)) == 2
        assert len(conversation_repo.get_user_conversations("user1", skip=4, limit=2)) == 1

    def test_count_user_conversations(self, conversation_repo):
        conversation_repo.create_conversation("Conv 1", "user1")
        conversation_repo.create_conversation("Conv 2", "user1")
        assert conversation_repo.count_user_conversations("user1") == 2

    def test_update_conversation(self, conversation_repo):
        conversation = conversation_repo.create_conversation(title="Old Title", user_id="user1")
        updated = conversation_repo.update_conversation(conversation.id, "New Title")
        assert updated is not None
        assert updated.title == "New Title"

    def test_update_conversation_not_found(self, conversation_repo):
        assert conversation_repo.update_conversation(99999, "New Title") is None

    def test_delete_conversation(self, conversation_repo):
        conversation = conversation_repo.create_conversation(title="To Delete", user_id="user1")
        assert conversation_repo.delete_conversation(conversation.id) is True
        assert conversation_repo.get_conversation_by_id(conversation.id) is None

    def test_delete_conversation_not_found(self, conversation_repo):
        assert conversation_repo.delete_conversation(99999) is False


class TestMessageRepository:

    def test_create_message(self, conversation_repo, message_repo):
        conversation = conversation_repo.create_conversation(title="Test", user_id="user1")
        message = message_repo.create_message(conversation_id=conversation.id, role="user", content="Hello, world!")
        assert message.id is not None
        assert message.role == MessageRole.USER
        assert message.content == "Hello, world!"

    def test_get_conversation_messages(self, conversation_repo, message_repo):
        conversation = conversation_repo.create_conversation(title="Test", user_id="user1")
        message_repo.create_message(conversation.id, "user", "Message 1")
        message_repo.create_message(conversation.id, "assistant", "Message 2")
        messages = message_repo.get_conversation_messages(conversation.id)
        assert len(messages) == 2

    def test_get_message_by_id(self, conversation_repo, message_repo):
        conversation = conversation_repo.create_conversation(title="Test", user_id="user1")
        created = message_repo.create_message(conversation.id, "user", "Test message")
        retrieved = message_repo.get_message_by_id(created.id)
        assert retrieved is not None
        assert retrieved.content == "Test message"

    def test_delete_message(self, conversation_repo, message_repo):
        conversation = conversation_repo.create_conversation(title="Test", user_id="user1")
        message = message_repo.create_message(conversation.id, "user", "To delete")
        assert message_repo.delete_message(message.id) is True
        assert message_repo.get_message_by_id(message.id) is None

    def test_delete_message_not_found(self, message_repo):
        assert message_repo.delete_message(99999) is False