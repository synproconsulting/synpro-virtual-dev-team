"""
Unit tests for user deletion functionality.

Tests the UserDeletionService and related functions for proper
deletion, authorization, and error handling.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from src.auth.delete_user import (
    UserDeletionService,
    UserDeletionError,
    UserNotFoundError,
    UnauthorizedDeletionError,
    delete_user_account
)


class TestUserDeletionService:
    """Test suite for UserDeletionService."""
    
    def test_initialization_default(self):
        """Test service initialization with default parameters."""
        service = UserDeletionService()
        assert service.db is None
        assert service.soft_delete_enabled is True
    
    def test_initialization_with_db(self):
        """Test service initialization with database connection."""
        mock_db = Mock()
        service = UserDeletionService(database_connection=mock_db)
        assert service.db is mock_db
    
    @patch.dict('os.environ', {'SOFT_DELETE_ENABLED': 'false'})
    def test_initialization_hard_delete_mode(self):
        """Test service initialization with hard delete enabled."""
        service = UserDeletionService()
        assert service.soft_delete_enabled is False
    
    def test_delete_own_account_soft_delete(self):
        """Test user deleting their own account with soft delete."""
        service = UserDeletionService()
        
        result = service.delete_user(
            user_id="user123",
            requesting_user_id="user123"
        )
        
        assert result["success"] is True
        assert result["user_id"] == "user123"
        assert result["deletion_type"] == "soft"
        assert "deleted_at" in result
    
    def test_delete_own_account_hard_delete(self):
        """Test user deleting their own account with hard delete."""
        service = UserDeletionService()
        
        result = service.delete_user(
            user_id="user123",
            requesting_user_id="user123",
            force_hard_delete=True
        )
        
        assert result["success"] is True
        assert result["user_id"] == "user123"
        assert result["deletion_type"] == "hard"
        assert result["user_removed"] is True
    
    def test_unauthorized_deletion_attempt(self):
        """Test that unauthorized deletion is blocked."""
        service = UserDeletionService()
        
        with pytest.raises(UnauthorizedDeletionError) as exc_info:
            service.delete_user(
                user_id="user123",
                requesting_user_id="user456"
            )
        
        assert "not authorized" in str(exc_info.value).lower()
    
    def test_admin_can_delete_other_user(self):
        """Test that admin can delete another user's account."""
        mock_db = Mock()
        mock_db.get_user_by_id = Mock(side_effect=[
            {"id": "user123", "is_admin": False},  # Target user
            {"id": "admin1", "is_admin": True}      # Requesting user
        ])
        
        service = UserDeletionService(database_connection=mock_db)
        
        # Mock the internal methods
        service._get_user = Mock(side_effect=[
            {"id": "user123", "is_admin": False},
            {"id": "admin1", "is_admin": True}
        ])
        
        result = service.delete_user(
            user_id="user123",
            requesting_user_id="admin1"
        )
        
        assert result["success"] is True
        assert result["user_id"] == "user123"
    
    def test_soft_delete_marks_user_inactive(self):
        """Test that soft delete marks user as inactive."""
        mock_db = Mock()
        mock_db.update_user = Mock()
        
        service = UserDeletionService(database_connection=mock_db)
        
        result = service._soft_delete_user("user123")
        
        assert result["marked_deleted"] is True
        assert result["data_retained"] is True
    
    def test_hard_delete_removes_all_data(self):
        """Test that hard delete removes all user data."""
        mock_db = Mock()
        mock_db.delete_user_sessions = Mock(return_value=5)
        mock_db.delete_user_tokens = Mock(return_value=3)
        mock_db.delete_user_profile = Mock(return_value=1)
        mock_db.delete_user = Mock()
        
        service = UserDeletionService(database_connection=mock_db)
        
        result = service._hard_delete_user("user123")
        
        assert result["user_removed"] is True
        assert result["sessions_removed"] == 5
        assert result["tokens_removed"] == 3
        assert result["profile_removed"] == 1
        assert result["data_removed"] is True
        
        # Verify cascade deletion order
        mock_db.delete_user_sessions.assert_called_once_with("user123")
        mock_db.delete_user_tokens.assert_called_once_with("user123")
        mock_db.delete_user_profile.assert_called_once_with("user123")
        mock_db.delete_user.assert_called_once_with("user123")
    
    def test_anonymize_user_success(self):
        """Test successful user anonymization."""
        service = UserDeletionService()
        
        result = service.anonymize_user("user123")
        
        assert result["success"] is True
        assert result["user_id"] == "user123"
        assert result["anonymized"] is True
        assert "anonymized_at" in result
    
    def test_anonymize_nonexistent_user(self):
        """Test anonymizing a user that doesn't exist."""
        service = UserDeletionService()
        service._get_user = Mock(return_value=None)
        
        with pytest.raises(UserNotFoundError):
            service.anonymize_user("nonexistent")
    
    def test_anonymize_user_with_database(self):
        """Test user anonymization with database."""
        mock_db = Mock()
        mock_db.update_user = Mock()
        
        service = UserDeletionService(database_connection=mock_db)
        
        result = service.anonymize_user("user123")
        
        # Verify anonymized data was saved
        mock_db.update_user.assert_called_once()
        call_args = mock_db.update_user.call_args
        assert call_args[0][0] == "user123"
        
        updated_data = call_args[0][1]
        assert updated_data["email"].startswith("deleted_")
        assert updated_data["username"].startswith("deleted_user_")
        assert updated_data["first_name"] == "Deleted"
        assert updated_data["last_name"] == "User"
        assert updated_data["is_active"] is False
    
    def test_is_authorized_self_deletion(self):
        """Test authorization check for self-deletion."""
        service = UserDeletionService()
        
        assert service._is_authorized("user123", "user123") is True
    
    def test_is_authorized_admin_deletion(self):
        """Test authorization check for admin deletion."""
        service = UserDeletionService()
        service._get_user = Mock(return_value={"id": "admin1", "is_admin": True})
        
        assert service._is_authorized("user123", "admin1") is True
    
    def test_is_authorized_non_admin_other_user(self):
        """Test authorization check for non-admin trying to delete other user."""
        service = UserDeletionService()
        service._get_user = Mock(return_value={"id": "user456", "is_admin": False})
        
        assert service._is_authorized("user123", "user456") is False
    
    def test_get_user_with_database(self):
        """Test user retrieval with database."""
        mock_db = Mock()
        mock_db.get_user_by_id = Mock(
            return_value={"id": "user123", "email": "test@example.com"}
        )
        
        service = UserDeletionService(database_connection=mock_db)
        
        user = service._get_user("user123")
        
        assert user is not None
        assert user["id"] == "user123"
        mock_db.get_user_by_id.assert_called_once_with("user123")
    
    def test_get_user_database_error(self):
        """Test user retrieval when database raises error."""
        mock_db = Mock()
        mock_db.get_user_by_id = Mock(side_effect=Exception("DB error"))
        
        service = UserDeletionService(database_connection=mock_db)
        
        user = service._get_user("user123")
        
        assert user is None


class TestDeleteUserAccountFunction:
    """Test suite for delete_user_account convenience function."""
    
    def test_delete_user_account_success(self):
        """Test successful user deletion via convenience function."""
        result = delete_user_account(
            user_id="user123",
            requesting_user_id="user123"
        )
        
        assert result["success"] is True
        assert result["user_id"] == "user123"
    
    def test_delete_user_account_with_db(self):
        """Test user deletion with database connection."""
        mock_db = Mock()
        
        result = delete_user_account(
            user_id="user123",
            requesting_user_id="user123",
            database_connection=mock_db
        )
        
        assert result["success"] is True
    
    def test_delete_user_account_hard_delete(self):
        """Test forced hard deletion via convenience function."""
        result = delete_user_account(
            user_id="user123",
            requesting_user_id="user123",
            force_hard_delete=True
        )
        
        assert result["success"] is True
        assert result["deletion_type"] == "hard"
    
    def test_delete_user_account_unauthorized(self):
        """Test unauthorized deletion via convenience function."""
        with pytest.raises(UnauthorizedDeletionError):
            delete_user_account(
                user_id="user123",
                requesting_user_id="user456"
            )


class TestExceptionClasses:
    """Test suite for custom exception classes."""
    
    def test_user_deletion_error(self):
        """Test UserDeletionError exception."""
        error = UserDeletionError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_user_not_found_error(self):
        """Test UserNotFoundError exception."""
        error = UserNotFoundError("User not found")
        assert str(error) == "User not found"
        assert isinstance(error, UserDeletionError)
    
    def test_unauthorized_deletion_error(self):
        """Test UnauthorizedDeletionError exception."""
        error = UnauthorizedDeletionError("Unauthorized")
        assert str(error) == "Unauthorized"
        assert isinstance(error, UserDeletionError)


@pytest.fixture
def mock_database():
    """Fixture providing a mock database connection."""
    db = Mock()
    db.get_user_by_id = Mock(return_value={
        "id": "user123",
        "email": "test@example.com",
        "is_admin": False
    })
    db.update_user = Mock()
    db.delete_user = Mock()
    db.delete_user_sessions = Mock(return_value=0)
    db.delete_user_tokens = Mock(return_value=0)
    db.delete_user_profile = Mock(return_value=0)
    return db


class TestIntegrationScenarios:
    """Integration tests for complete deletion scenarios."""
    
    def test_complete_soft_delete_flow(self, mock_database):
        """Test complete soft delete flow with database."""
        service = UserDeletionService(database_connection=mock_database)
        
        result = service.delete_user(
            user_id="user123",
            requesting_user_id="user123",
            force_hard_delete=False
        )
        
        assert result["success"] is True
        assert result["deletion_type"] == "soft"
        mock_database.update_user.assert_called_once()
    
    def test_complete_hard_delete_flow(self, mock_database):
        """Test complete hard delete flow with database."""
        service = UserDeletionService(database_connection=mock_database)
        
        result = service.delete_user(
            user_id="user123",
            requesting_user_id="user123",
            force_hard_delete=True
        )
        
        assert result["success"] is True
        assert result["deletion_type"] == "hard"
        assert result["user_removed"] is True
        
        # Verify all deletion methods were called
        mock_database.delete_user_sessions.assert_called_once()
        mock_database.delete_user_tokens.assert_called_once()
        mock_database.delete_user_profile.assert_called_once()
        mock_database.delete_user.assert_called_once()
