"""
Tests for user storage implementations.
"""

import pytest
from src.auth.storage import InMemoryUserStorage
from src.auth.models import User


class TestInMemoryUserStorage:
    """Test cases for in-memory user storage."""
    
    def test_save_user(self):
        """Test saving a user."""
        storage = InMemoryUserStorage()
        user = User(email="test@example.com", hashed_password="hashed")
        
        saved_user = storage.save_user(user)
        
        assert saved_user.user_id is not None
        assert saved_user.email == "test@example.com"
    
    def test_save_user_generates_id(self):
        """Test that user ID is generated if not provided."""
        storage = InMemoryUserStorage()
        user = User(email="test@example.com", hashed_password="hashed")
        
        assert user.user_id is None
        
        saved_user = storage.save_user(user)
        
        assert saved_user.user_id is not None
        assert len(saved_user.user_id) > 0
    
    def test_get_user_by_email(self):
        """Test retrieving user by email."""
        storage = InMemoryUserStorage()
        user = User(email="test@example.com", hashed_password="hashed")
        storage.save_user(user)
        
        retrieved_user = storage.get_user_by_email("test@example.com")
        
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
    
    def test_get_user_by_email_case_insensitive(self):
        """Test that email lookup is case-insensitive."""
        storage = InMemoryUserStorage()
        user = User(email="Test@Example.COM", hashed_password="hashed")
        storage.save_user(user)
        
        retrieved_user = storage.get_user_by_email("test@example.com")
        
        assert retrieved_user is not None
        assert retrieved_user.email == "Test@Example.COM"
    
    def test_get_user_by_email_not_found(self):
        """Test that None is returned for non-existent email."""
        storage = InMemoryUserStorage()
        
        retrieved_user = storage.get_user_by_email("nonexistent@example.com")
        
        assert retrieved_user is None
    
    def test_get_user_by_id(self):
        """Test retrieving user by ID."""
        storage = InMemoryUserStorage()
        user = User(email="test@example.com", hashed_password="hashed")
        saved_user = storage.save_user(user)
        
        retrieved_user = storage.get_user_by_id(saved_user.user_id)
        
        assert retrieved_user is not None
        assert retrieved_user.user_id == saved_user.user_id
    
    def test_get_user_by_id_not_found(self):
        """Test that None is returned for non-existent ID."""
        storage = InMemoryUserStorage()
        
        retrieved_user = storage.get_user_by_id("nonexistent-id")
        
        assert retrieved_user is None
    
    def test_email_exists(self):
        """Test checking if email exists."""
        storage = InMemoryUserStorage()
        user = User(email="test@example.com", hashed_password="hashed")
        storage.save_user(user)
        
        assert storage.email_exists("test@example.com") is True
        assert storage.email_exists("other@example.com") is False
    
    def test_email_exists_case_insensitive(self):
        """Test that email existence check is case-insensitive."""
        storage = InMemoryUserStorage()
        user = User(email="Test@Example.COM", hashed_password="hashed")
        storage.save_user(user)
        
        assert storage.email_exists("test@example.com") is True
        assert storage.email_exists("TEST@EXAMPLE.COM") is True
    
    def test_multiple_users(self):
        """Test storing and retrieving multiple users."""
        storage = InMemoryUserStorage()
        
        user1 = User(email="user1@example.com", hashed_password="hash1")
        user2 = User(email="user2@example.com", hashed_password="hash2")
        
        saved1 = storage.save_user(user1)
        saved2 = storage.save_user(user2)
        
        assert storage.get_user_by_email("user1@example.com") == saved1
        assert storage.get_user_by_email("user2@example.com") == saved2
        assert storage.get_user_by_id(saved1.user_id) == saved1
        assert storage.get_user_by_id(saved2.user_id) == saved2
