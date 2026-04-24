"""
Unit tests for user account deletion functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import psycopg2

from src.auth.delete_user import (
    delete_user_account,
    verify_user_exists,
    verify_deletion_authorization,
    soft_delete_user,
    hard_delete_user,
    bulk_delete_inactive_users,
    get_database_connection,
    UserDeletionError,
    UserNotFoundError,
    UnauthorizedDeletionError
)


class TestVerifyDeletionAuthorization:
    """Tests for deletion authorization verification."""
    
    def test_user_can_delete_own_account(self):
        """Test that a user can delete their own account."""
        # Should not raise an exception
        verify_deletion_authorization(
            user_id=1,
            requesting_user_id=1,
            is_admin=False
        )
    
    def test_user_cannot_delete_other_account(self):
        """Test that a non-admin user cannot delete another user's account."""
        with pytest.raises(UnauthorizedDeletionError):
            verify_deletion_authorization(
                user_id=1,
                requesting_user_id=2,
                is_admin=False
            )
    
    def test_admin_can_delete_any_account(self):
        """Test that an admin can delete any user's account."""
        # Should not raise an exception
        verify_deletion_authorization(
            user_id=1,
            requesting_user_id=2,
            is_admin=True
        )


class TestVerifyUserExists:
    """Tests for user existence verification."""
    
    def test_user_exists(self):
        """Test that existing user is returned correctly."""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'email': 'test@example.com',
            'username': 'testuser',
            'is_active': True
        }
        
        user = verify_user_exists(1, mock_cursor)
        
        assert user['id'] == 1
        assert user['email'] == 'test@example.com'
        mock_cursor.execute.assert_called_once()
    
    def test_user_not_found(self):
        """Test that exception is raised when user is not found."""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        
        with pytest.raises(UserNotFoundError):
            verify_user_exists(999, mock_cursor)


class TestSoftDeleteUser:
    """Tests for soft deletion functionality."""
    
    @patch('src.auth.delete_user.datetime')
    def test_soft_delete_user(self, mock_datetime):
        """Test that soft delete properly anonymizes user data."""
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        
        mock_cursor = Mock()
        
        soft_delete_user(1, mock_cursor)
        
        # Verify UPDATE query was called
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        
        # Check that the query contains expected elements
        query = call_args[0][0]
        assert 'UPDATE users' in query
        assert 'is_active = FALSE' in query
        assert 'deleted_at' in query


class TestHardDeleteUser:
    """Tests for hard deletion functionality."""
    
    def test_hard_delete_user(self):
        """Test that hard delete removes user and all related data."""
        mock_cursor = Mock()
        
        hard_delete_user(1, mock_cursor)
        
        # Should execute 4 DELETE queries
        assert mock_cursor.execute.call_count == 4
        
        # Verify related data is deleted first
        calls = [call[0][0] for call in mock_cursor.execute.call_args_list]
        assert any('user_sessions' in call for call in calls)
        assert any('user_tokens' in call for call in calls)
        assert any('user_preferences' in call for call in calls)
        assert any('DELETE FROM users' in call for call in calls)


class TestDeleteUserAccount:
    """Tests for the main delete_user_account function."""
    
    @patch('src.auth.delete_user.get_database_connection')
    def test_successful_soft_delete(self, mock_get_conn):
        """Test successful soft deletion of user account."""
        # Setup mocks
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'email': 'test@example.com',
            'username': 'testuser',
            'is_active': True
        }
        
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        # Execute
        result = delete_user_account(
            user_id=1,
            requesting_user_id=1,
            is_admin=False,
            hard_delete=False
        )
        
        # Verify
        assert result['success'] is True
        assert result['user_id'] == 1
        assert result['deletion_type'] == 'soft'
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
    
    @patch('src.auth.delete_user.get_database_connection')
    def test_successful_hard_delete(self, mock_get_conn):
        """Test successful hard deletion of user account."""
        # Setup mocks
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'email': 'test@example.com',
            'username': 'testuser',
            'is_active': True
        }
        
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        # Execute
        result = delete_user_account(
            user_id=1,
            requesting_user_id=1,
            is_admin=False,
            hard_delete=True
        )
        
        # Verify
        assert result['success'] is True
        assert result['user_id'] == 1
        assert result['deletion_type'] == 'hard'
        mock_conn.commit.assert_called_once()
    
    @patch('src.auth.delete_user.get_database_connection')
    def test_unauthorized_deletion(self, mock_get_conn):
        """Test that unauthorized deletion raises exception."""
        with pytest.raises(UnauthorizedDeletionError):
            delete_user_account(
                user_id=1,
                requesting_user_id=2,
                is_admin=False,
                hard_delete=False
            )
    
    @patch('src.auth.delete_user.get_database_connection')
    def test_user_not_found(self, mock_get_conn):
        """Test deletion of non-existent user."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        
        mock_cursor.fetchone.return_value = None
        
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        with pytest.raises(UserNotFoundError):
            delete_user_account(
                user_id=999,
                requesting_user_id=999,
                is_admin=False,
                hard_delete=False
            )
        
        mock_conn.rollback.assert_called()
    
    @patch('src.auth.delete_user.get_database_connection')
    def test_database_error_rollback(self, mock_get_conn):
        """Test that database errors trigger rollback."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'email': 'test@example.com',
            'username': 'testuser',
            'is_active': True
        }
        
        # Simulate database error on execute
        mock_cursor.execute.side_effect = psycopg2.DatabaseError("DB Error")
        
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        with pytest.raises(UserDeletionError):
            delete_user_account(
                user_id=1,
                requesting_user_id=1,
                is_admin=False,
                hard_delete=False
            )
        
        mock_conn.rollback.assert_called()
        mock_conn.close.assert_called_once()


class TestBulkDeleteInactiveUsers:
    """Tests for bulk deletion of inactive users."""
    
    @patch('src.auth.delete_user.get_database_connection')
    def test_bulk_delete_dry_run(self, mock_get_conn):
        """Test bulk deletion in dry-run mode."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'email': 'user1@example.com', 'username': 'user1'},
            {'id': 2, 'email': 'user2@example.com', 'username': 'user2'}
        ]
        
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        result = bulk_delete_inactive_users(
            days_inactive=365,
            requesting_admin_id=1,
            dry_run=True
        )
        
        assert result['success'] is True
        assert result['dry_run'] is True
        assert result['users_to_delete'] == 2
        mock_conn.commit.assert_not_called()
    
    @patch('src.auth.delete_user.get_database_connection')
    def test_bulk_delete_actual(self, mock_get_conn):
        """Test actual bulk deletion of inactive users."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'email': 'user1@example.com', 'username': 'user1'},
            {'id': 2, 'email': 'user2@example.com', 'username': 'user2'}
        ]
        
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        result = bulk_delete_inactive_users(
            days_inactive=365,
            requesting_admin_id=1,
            dry_run=False
        )
        
        assert result['success'] is True
        assert result['dry_run'] is False
        assert result['users_deleted'] == 2
        mock_conn.commit.assert_called_once()


class TestGetDatabaseConnection:
    """Tests for database connection function."""
    
    @patch.dict('os.environ', {
        'DB_HOST': 'localhost',
        'DB_NAME': 'testdb',
        'DB_USER': 'testuser',
        'DB_PASSWORD': 'testpass',
        'DB_PORT': '5432'
    })
    @patch('src.auth.delete_user.psycopg2.connect')
    def test_successful_connection(self, mock_connect):
        """Test successful database connection."""
        mock_connect.return_value = Mock()
        
        conn = get_database_connection()
        
        mock_connect.assert_called_once_with(
            host='localhost',
            database='testdb',
            user='testuser',
            password='testpass',
            port='5432'
        )
    
    @patch.dict('os.environ', {}, clear=True)
    def test_missing_environment_variables(self):
        """Test that missing environment variables raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_database_connection()
        
        assert 'Missing required environment variables' in str(exc_info.value)
