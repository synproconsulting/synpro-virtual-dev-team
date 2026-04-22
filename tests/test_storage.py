"""
Unit tests for user storage functionality.
"""
import pytest
from src.auth.storage import UserStorage
from src.auth.models import User


class TestUserStorage:
    """Test cases for UserStorage."""
    
    def test_save_and_retrieve_user_by_id(self):
        """Test saving and retrieving a user by ID."""
        storage = UserStorage()
        user = User(email="test@example.com", password_hash="hashed_password")
        
        storage.save_user(user)
        retrieved = storage.get_user_by_id(user.id)
        
        assert retrieved is not None
        assert retrieved.id == user.id
        assert retrieved.email == user.email
    
    def test_save_and_retrieve_user_by_email(self):
        """Test saving and retrieving a user by email."""
        storage = UserStorage()
        user = User(email="test@example.com", password_hash="hashed_password")
        
        storage.save_user(user)
        retrieved = storage.get_user_by_email("test@example.com")
        
        assert retrieved is not None
        assert retrieved.email == user.email
    
    def test_email_case_insensitive(self):
        """Test that email lookups are case insensitive."""
        storage = UserStorage()
        user = User(email="Test@Example.COM", password_hash="hashed_password")
        
        storage.save_user(user)
        retrieved = storage.get_user_by_email("test@example.com")
        
        assert retrieved is not None
        assert retrieved.id == user.id
    
    def test_email_exists(self):
        """Test checking if email exists."""
        storage = UserStorage()
        user = User(email="test@example.com", password_hash="hashed_password")
        
        assert storage.email_exists("test@example.com") is False
        
        storage.save_user(user)
        
        assert storage.email_exists("test@example.com") is True
        assert storage.email_exists("TEST@EXAMPLE.COM") is True
    
    def test_get_nonexistent_user_by_id(self):
        """Test retrieving a user that doesn't exist by ID."""
        storage = UserStorage()
        retrieved = storage.get_user_by_id("nonexistent-id")
        
        assert retrieved is None
    
    def test_get_nonexistent_user_by_email(self):
        """Test retrieving a user that doesn't exist by email."""
        storage = UserStorage()
        retrieved = storage.get_user_by_email("nonexistent@example.com")
        
        assert retrieved is None
    
    def test_delete_user(self):
        """Test deleting a user."""
        storage = UserStorage()
        user = User(email="test@example.com", password_hash="hashed_password")
        
        storage.save_user(user)
        assert storage.email_exists("test@example.com") is True
        
        result = storage.delete_user(user.id)
        
        assert result is True
        assert storage.email_exists("test@example.com") is False
        assert storage.get_user_by_id(user.id) is None
    
    def test_delete_nonexistent_user(self):
        """Test deleting a user that doesn't exist."""
        storage = UserStorage()
        result = storage.delete_user("nonexistent-id")
        
        assert result is False
