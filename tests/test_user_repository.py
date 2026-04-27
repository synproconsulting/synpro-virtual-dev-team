"""Tests for user repository."""

import pytest
from src.auth.credentials import UserRecord
from src.auth.user_repository import InMemoryUserRepository


class TestInMemoryUserRepository:
    """Test cases for InMemoryUserRepository."""
    
    def test_save_and_retrieve_user(self) -> None:
        """Test saving and retrieving a user."""
        repo = InMemoryUserRepository()
        user = UserRecord(
            username="testuser",
            password_hash="hash123",
            salt="salt123",
            user_id="user_1"
        )
        
        repo.save_user(user)
        retrieved = repo.get_user_by_username("testuser")
        
        assert retrieved is not None
        assert retrieved.username == "testuser"
        assert retrieved.password_hash == "hash123"
        assert retrieved.salt == "salt123"
        assert retrieved.user_id == "user_1"
    
    def test_get_nonexistent_user(self) -> None:
        """Test retrieving a user that doesn't exist."""
        repo = InMemoryUserRepository()
        result = repo.get_user_by_username("nonexistent")
        
        assert result is None
    
    def test_update_user(self) -> None:
        """Test updating an existing user."""
        repo = InMemoryUserRepository()
        user1 = UserRecord(
            username="testuser",
            password_hash="hash1",
            salt="salt1"
        )
        user2 = UserRecord(
            username="testuser",
            password_hash="hash2",
            salt="salt2",
            is_active=False
        )
        
        repo.save_user(user1)
        repo.save_user(user2)
        
        retrieved = repo.get_user_by_username("testuser")
        assert retrieved is not None
        assert retrieved.password_hash == "hash2"
        assert retrieved.is_active is False
