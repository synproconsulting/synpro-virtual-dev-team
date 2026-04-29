"""
Unit tests for conversation and message schemas.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.chat.schemas import (
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
    """Tests for message schemas."""

    def test_message_base_valid(self):
        """Test valid MessageBase schema."""
        message = MessageBase(
            role="user",
            content="Hello, world!"
        )
        assert message.role == "user"
        assert message.content == "Hello, world!"

    def test_message_base_empty_content(self):
        """Test MessageBase with empty content should fail."""
        with pytest.raises(ValidationError):
            MessageBase(role="user", content="")

    def test_message_create_valid(self):
        """Test valid MessageCreate schema."""
        message = MessageCreate(
            conversation_id=1,
            role="assistant",
            content="Hi there!"
        )
        assert message.conversation_id == 1
        assert message.role == "assistant"
        assert message.content == "Hi there!"

    def test_message_create_invalid_conversation_id(self):
        """Test MessageCreate with invalid conversation_id."""
        with pytest.raises(ValidationError):
            MessageCreate(
                conversation_id=0,
                role="user",
                content="Test"
            )

    def test_message_response_valid(self):
        """Test valid MessageResponse schema."""
        now = datetime.utcnow()
        message = MessageResponse(
            id=1,
            conversation_id=5,
            role="user",
            content="Test message",
            created_at=now
        )
        assert message.id == 1
        assert message.conversation_id == 5
        assert message.role == "user"
        assert message.content == "Test message"
        assert message.created_at == now


class TestConversationSchemas:
    """Tests for conversation schemas."""

    def test_conversation_base_valid(self):
        """Test valid ConversationBase schema."""
        conversation = ConversationBase(title="My Conversation")
        assert conversation.title == "My Conversation"

    def test_conversation_base_empty_title(self):
        """Test ConversationBase with empty title should fail."""
        with pytest.raises(ValidationError):
            ConversationBase(title="")

    def test_conversation_base_too_long_title(self):
        """Test ConversationBase with title exceeding max length."""
        with pytest.raises(ValidationError):
            ConversationBase(title="a" * 256)

    def test_conversation_create_valid(self):
        """Test valid ConversationCreate schema."""
        conversation = ConversationCreate(
            title="New Conversation",
            user_id="user123"
        )
        assert conversation.title == "New Conversation"
        assert conversation.user_id == "user123"

    def test_conversation_create_empty_user_id(self):
        """Test ConversationCreate with empty user_id should fail."""
        with pytest.raises(ValidationError):
            ConversationCreate(
                title="Test",
                user_id=""
            )

    def test_conversation_update_valid(self):
        """Test valid ConversationUpdate schema."""
        update = ConversationUpdate(title="Updated Title")
        assert update.title == "Updated Title"

    def test_conversation_update_optional_title(self):
        """Test ConversationUpdate with no title (optional)."""
        update = ConversationUpdate()
        assert update.title is None

    def test_conversation_response_valid(self):
        """Test valid ConversationResponse schema."""
        now = datetime.utcnow()
        conversation = ConversationResponse(
            id=1,
            title="Test Conversation",
            user_id="user123",
            created_at=now,
            updated_at=now
        )
        assert conversation.id == 1
        assert conversation.title == "Test Conversation"
        assert conversation.user_id == "user123"
        assert conversation.created_at == now
        assert conversation.updated_at == now

    def test_conversation_with_messages_valid(self):
        """Test valid ConversationWithMessages schema."""
        now = datetime.utcnow()
        
        message1 = MessageResponse(
            id=1,
            conversation_id=1,
            role="user",
            content="Hello",
            created_at=now
        )
        
        message2 = MessageResponse(
            id=2,
            conversation_id=1,
            role="assistant",
            content="Hi there!",
            created_at=now
        )
        
        conversation = ConversationWithMessages(
            id=1,
            title="Test Conversation",
            user_id="user123",
            created_at=now,
            updated_at=now,
            messages=[message1, message2]
        )
        
        assert conversation.id == 1
        assert len(conversation.messages) == 2
        assert conversation.messages[0].content == "Hello"
        assert conversation.messages[1].content == "Hi there!"

    def test_conversation_with_messages_empty_list(self):
        """Test ConversationWithMessages with empty message list."""
        now = datetime.utcnow()
        conversation = ConversationWithMessages(
            id=1,
            title="Test Conversation",
            user_id="user123",
            created_at=now,
            updated_at=now,
            messages=[]
        )
        assert len(conversation.messages) == 0

    def test_conversation_list_response_valid(self):
        """Test valid ConversationListResponse schema."""
        now = datetime.utcnow()
        
        conv1 = ConversationResponse(
            id=1,
            title="Conv 1",
            user_id="user1",
            created_at=now,
            updated_at=now
        )
        
        conv2 = ConversationResponse(
            id=2,
            title="Conv 2",
            user_id="user1",
            created_at=now,
            updated_at=now
        )
        
        response = ConversationListResponse(
            conversations=[conv1, conv2],
            total=10,
            page=1,
            page_size=2
        )
        
        assert len(response.conversations) == 2
        assert response.total == 10
        assert response.page == 1
        assert response.page_size == 2

    def test_conversation_list_response_negative_total(self):
        """Test ConversationListResponse with negative total should fail."""
        with pytest.raises(ValidationError):
            ConversationListResponse(
                conversations=[],
                total=-1,
                page=1,
                page_size=10
            )

    def test_conversation_list_response_invalid_page(self):
        """Test ConversationListResponse with invalid page should fail."""
        with pytest.raises(ValidationError):
            ConversationListResponse(
                conversations=[],
                total=0,
                page=0,
                page_size=10
            )
