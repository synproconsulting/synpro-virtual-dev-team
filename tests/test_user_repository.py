"""
Unit tests for user repository.
"""

import pytest
from src.auth.user_repository import InMemoryUserRepository


@pytest.fixture
def repository():
    """Create a fresh repository for each test."""
    return InMemoryUserRepository()


class TestCreateUser:
    """Test user creation."""
    
    def test_create_user_success(self, repository):
        """Test successful user creation."""
        user = repository.create(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed123"
        )
        
        assert user["id"] == 1
        assert user["username"] == "testuser"
        assert user["email"] == "test@example.com"
        assert user["hashed_password"] == "hashed123"
        assert "created_at" in user
        assert "updated_at" in user
    
    def test_create_multiple_users(self, repository):
        """Test creating multiple users increments IDs."""
        user1 = repository.create("user1", "user1@example.com", "hash1")
        user2 = repository.create("user2", "user2@example.com", "hash2")
        
        assert user1["id"] == 1
        assert user2["id"] == 2


class TestGetUser:
    """Test user retrieval."""
    
    def test_get_by_id_success(self, repository):
        """Test retrieving user by ID."""
        created_user = repository.create("testuser", "test@example.com", "hash")
        
        user = repository.get_by_id(created_user["id"])
        assert user is not None
        assert user["id"] == created_user["id"]
        assert user["username"] == "testuser"
    
    def test_get_by_id_not_found(self, repository):
        """Test retrieving non-existent user returns None."""
        user = repository.get_by_id(999)
        assert user is None
    
    def test_get_by_username_success(self, repository):
        """Test retrieving user by username."""
        repository.create("testuser", "test@example.com", "hash")
        
        user = repository.get_by_username("testuser")
        assert user is not None
        assert user["username"] == "testuser"
    
    def test_get_by_username_not_found(self, repository):
        """Test retrieving non-existent username returns None."""
        user = repository.get_by_username("nonexistent")
        assert user is None
    
    def test_get_by_email_success(self, repository):
        """Test retrieving user by email."""
        repository.create("testuser", "test@example.com", "hash")
        
        user = repository.get_by_email("test@example.com")
        assert user is not None
        assert user["email"] == "test@example.com"
    
    def test_get_by_email_not_found(self, repository):
        """Test retrieving non-existent email returns None."""
        user = repository.get_by_email("nonexistent@example.com")
        assert user is None


class TestUpdateUsername:
    """Test username update."""
    
    def test_update_username_success(self, repository):
        """Test successful username update."""
        user = repository.create("oldname", "test@example.com", "hash")
        
        updated = repository.update_username(user["id"], "newname")
        
        assert updated["username"] == "newname"
        assert updated["email"] == "test@example.com"
        assert "updated_at" in updated
    
    def test_update_username_not_found(self, repository):
        """Test updating non-existent user raises error."""
        with pytest.raises(ValueError, match="not found"):
            repository.update_username(999, "newname")


class TestUpdateEmail:
    """Test email update."""
    
    def test_update_email_success(self, repository):
        """Test successful email update."""
        user = repository.create("testuser", "old@example.com", "hash")
        
        updated = repository.update_email(user["id"], "new@example.com")
        
        assert updated["email"] == "new@example.com"
        assert updated["username"] == "testuser"
        assert "updated_at" in updated
    
    def test_update_email_not_found(self, repository):
        """Test updating non-existent user raises error."""
        with pytest.raises(ValueError, match="not found"):
            repository.update_email(999, "new@example.com")


class TestUpdateProfile:
    """Test profile update."""
    
    def test_update_profile_both_fields(self, repository):
        """Test updating both username and email."""
        user = repository.create("oldname", "old@example.com", "hash")
        
        updated = repository.update_profile(
            user["id"],
            username="newname",
            email="new@example.com"
        )
        
        assert updated["username"] == "newname"
        assert updated["email"] == "new@example.com"
    
    def test_update_profile_username_only(self, repository):
        """Test updating only username."""
        user = repository.create("oldname", "test@example.com", "hash")
        
        updated = repository.update_profile(user["id"], username="newname")
        
        assert updated["username"] == "newname"
        assert updated["email"] == "test@example.com"
    
    def test_update_profile_email_only(self, repository):
        """Test updating only email."""
        user = repository.create("testuser", "old@example.com", "hash")
        
        updated = repository.update_profile(user["id"], email="new@example.com")
        
        assert updated["username"] == "testuser"
        assert updated["email"] == "new@example.com"
    
    def test_update_profile_not_found(self, repository):
        """Test updating non-existent user raises error."""
        with pytest.raises(ValueError, match="not found"):
            repository.update_profile(999, username="newname")


class TestDeleteUser:
    """Test user deletion."""
    
    def test_delete_success(self, repository):
        """Test successful user deletion."""
        user = repository.create("testuser", "test@example.com", "hash")
        
        result = repository.delete(user["id"])
        assert result is True
        
        # Verify user is actually deleted
        assert repository.get_by_id(user["id"]) is None
    
    def test_delete_not_found(self, repository):
        """Test deleting non-existent user returns False."""
        result = repository.delete(999)
        assert result is False


class TestListAll:
    """Test listing all users."""
    
    def test_list_all_empty(self, repository):
        """Test listing when no users exist."""
        users = repository.list_all()
        assert users == []
    
    def test_list_all_multiple_users(self, repository):
        """Test listing multiple users."""
        repository.create("user1", "user1@example.com", "hash1")
        repository.create("user2", "user2@example.com", "hash2")
        repository.create("user3", "user3@example.com", "hash3")
        
        users = repository.list_all()
        assert len(users) == 3
        
        usernames = [u["username"] for u in users]
        assert "user1" in usernames
        assert "user2" in usernames
        assert "user3" in usernames
