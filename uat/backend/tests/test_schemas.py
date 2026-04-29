"""Unit tests for conversation and message schemas."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from schemas import (
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


class TestMessageSchemas:

    def test_message_base_valid(self):
        message = MessageBase(role="user", content="Hello, world!")
        assert message.role == "user"
        assert message.content == "Hello, world!"

    def test_message_base_empty_content(self):
        with pytest.raises(ValidationError):
            MessageBase(role="user", content="")

    def test_message_create_valid(self):
        message = MessageCreate(conversation_id=1, role="assistant", content="Hi there!")
        assert message.conversation_id == 1

    def test_message_create_invalid_conversation_id(self):
        with pytest.raises(ValidationError):
            MessageCreate(conversation_id=0, role="user", content="Test")

    def test_message_response_valid(self):
        now = datetime.utcnow()
        message = MessageResponse(id=1, conversation_id=5, role="user", content="Test message", created_at=now)
        assert message.id == 1
        assert message.created_at == now


class TestConversationSchemas:

    def test_conversation_base_valid(self):
        conversation = ConversationBase(title="My Conversation")
        assert conversation.title == "My Conversation"

    def test_conversation_base_empty_title(self):
        with pytest.raises(ValidationError):
            ConversationBase(title="")

    def test_conversation_base_too_long_title(self):
        with pytest.raises(ValidationError):
            ConversationBase(title="a" * 256)

    def test_conversation_create_valid(self):
        conversation = ConversationCreate(title="New Conversation", user_id="user123")
        assert conversation.user_id == "user123"

    def test_conversation_create_empty_user_id(self):
        with pytest.raises(ValidationError):
            ConversationCreate(title="Test", user_id="")

    def test_conversation_update_optional_title(self):
        update = ConversationUpdate()
        assert update.title is None

    def test_conversation_response_valid(self):
        now = datetime.utcnow()
        conversation = ConversationResponse(id=1, title="Test", user_id="user123", created_at=now, updated_at=now)
        assert conversation.id == 1

    def test_conversation_with_messages_valid(self):
        now = datetime.utcnow()
        msg = MessageResponse(id=1, conversation_id=1, role="user", content="Hello", created_at=now)
        conversation = ConversationWithMessages(
            id=1, title="Test", user_id="user123", created_at=now, updated_at=now, messages=[msg]
        )
        assert len(conversation.messages) == 1

    def test_conversation_list_response_valid(self):
        now = datetime.utcnow()
        conv = ConversationResponse(id=1, title="Conv 1", user_id="user1", created_at=now, updated_at=now)
        response = ConversationListResponse(conversations=[conv], total=10, page=1, page_size=2)
        assert response.total == 10

    def test_conversation_list_response_negative_total(self):
        with pytest.raises(ValidationError):
            ConversationListResponse(conversations=[], total=-1, page=1, page_size=10)

    def test_conversation_list_response_invalid_page(self):
        with pytest.raises(ValidationError):
            ConversationListResponse(conversations=[], total=0, page=0, page_size=10)