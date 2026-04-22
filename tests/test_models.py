"""
Unit tests for user models.
"""
import pytest
from datetime import datetime
from src.auth.models import User


class TestUser:
    """Test cases for User model."""
    
    def test_user_creation(self):
        """Test basic user creation."""
        user = User(
            email="test@example.com",
            password_hash="hashed_password"
        )
        
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.id is not None
        assert user.is_active is True
        assert user.is_verified is False
    
    def test_user_unique_ids(self):
        """Test that each user gets a unique ID."""
        user1 = User(email="user1@example.com", password_hash="hash1")
        user2 = User(email="user2@example.com", password_hash="hash2")
        
        assert user1.id != user2.id
    
    def test_user_created_at_timestamp(self):
        """Test that created_at is set automatically."""
        user = User(email="test@example.com", password_hash="hashed_password")
        
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)
    
    def test_user_to_dict(self):
        """Test converting user to dictionary."""
        user = User(email="test@example.com", password_hash="hashed_password")
        user_dict = user.to_dict()
        
        assert "id" in user_dict
        assert "email" in user_dict
        assert "created_at" in user_dict
        assert "is_active" in user_dict
        assert "is_verified" in user_dict
        assert "password_hash" not in user_dict  # Should not expose password
    
    def test_user_to_dict_values(self):
        """Test that to_dict returns correct values."""
        user = User(email="test@example.com", password_hash="hashed_password")
        user_dict = user.to_dict()
        
        assert user_dict["email"] == "test@example.com"
        assert user_dict["id"] == user.id
        assert user_dict["is_active"] is True
        assert user_dict["is_verified"] is False
