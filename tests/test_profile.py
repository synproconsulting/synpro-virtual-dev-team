"""
Unit tests for user profile viewing functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.auth.profile import (
    UserProfile,
    UserProfileError,
    UserNotFoundError,
    DatabaseConnectionError
)


@pytest.fixture
def mock_database_url():
    """Provide a mock database URL for testing."""
    return "postgresql://user:password@localhost:5432/testdb"


@pytest.fixture
def user_profile(mock_database_url):
    """Create UserProfile instance with mock database URL."""
    return UserProfile(database_url=mock_database_url)


@pytest.fixture
def sample_user_data():
    """Provide sample user data for testing."""
    return {
        'id': 1,
        'username': 'johndoe',
        'email': 'john.doe@example.com',
        'full_name': 'John Doe',
        'bio': 'Software developer and tech enthusiast',
        'avatar_url': 'https://example.com/avatars/johndoe.png',
        'created_at': datetime(2024, 1, 1, 10, 0, 0),
        'updated_at': datetime(2024, 1, 15, 14, 30, 0),
        'last_login': datetime(2024, 1, 20, 9, 15, 0)
    }


class TestUserProfileInitialization:
    """Test UserProfile initialization."""
    
    def test_init_with_database_url(self, mock_database_url):
        """Test initialization with provided database URL."""
        profile = UserProfile(database_url=mock_database_url)
        assert profile.database_url == mock_database_url
    
    def test_init_with_env_variable(self, monkeypatch, mock_database_url):
        """Test initialization with environment variable."""
        monkeypatch.setenv('DATABASE_URL', mock_database_url)
        profile = UserProfile()
        assert profile.database_url == mock_database_url
    
    def test_init_without_database_url(self, monkeypatch):
        """Test initialization fails without database URL."""
        monkeypatch.delenv('DATABASE_URL', raising=False)
        with pytest.raises(DatabaseConnectionError):
            UserProfile()


class TestGetProfileById:
    """Test get_profile_by_id method."""
    
    @patch('src.auth.profile.psycopg2.connect')
    def test_get_profile_by_id_success(self, mock_connect, user_profile, sample_user_data):
        """Test successful retrieval of user profile by ID."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_user_data
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_connect.return_value = mock_conn
        
        result = user_profile.get_profile_by_id(1)
        
        assert result['id'] == 1
        assert result['username'] == 'johndoe'
        assert result['email'] == 'john.doe@example.com'
        mock_cursor.execute.assert_called_once()
    
    @patch('src.auth.profile.psycopg2.connect')
    def test_get_profile_by_id_not_found(self, mock_connect, user_profile):
        """Test retrieval fails when user not found."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_connect.return_value = mock_conn
        
        with pytest.raises(UserNotFoundError) as exc_info:
            user_profile.get_profile_by_id(999)
        
        assert "User with ID 999 not found" in str(exc_info.value)
    
    @patch('src.auth.profile.psycopg2.connect')
    def test_get_profile_by_id_database_error(self, mock_connect, user_profile):
        """Test handling of database errors."""
        import psycopg2
        mock_connect.side_effect = psycopg2.OperationalError("Connection failed")
        
        with pytest.raises(DatabaseConnectionError):
            user_profile.get_profile_by_id(1)


class TestGetProfileByUsername:
    """Test get_profile_by_username method."""
    
    @patch('src.auth.profile.psycopg2.connect')
    def test_get_profile_by_username_success(self, mock_connect, user_profile, sample_user_data):
        """Test successful retrieval of user profile by username."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = sample_user_data
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_connect.return_value = mock_conn
        
        result = user_profile.get_profile_by_username('johndoe')
        
        assert result['username'] == 'johndoe'
        assert result['email'] == 'john.doe@example.com'
        mock_cursor.execute.assert_called_once()
    
    @patch('src.auth.profile.psycopg2.connect')
    def test_get_profile_by_username_not_found(self, mock_connect, user_profile):
        """Test retrieval fails when username not found."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_connect.return_value = mock_conn
        
        with pytest.raises(UserNotFoundError) as exc_info:
            user_profile.get_profile_by_username('nonexistent')
        
        assert "User with username 'nonexistent' not found" in str(exc_info.value)


class TestGetPublicProfile:
    """Test get_public_profile method."""
    
    @patch.object(UserProfile, 'get_profile_by_id')
    def test_get_public_profile_filters_sensitive_data(self, mock_get_profile, user_profile, sample_user_data):
        """Test that public profile excludes sensitive information."""
        mock_get_profile.return_value = sample_user_data
        
        result = user_profile.get_public_profile(1)
        
        # Public fields should be present
        assert 'id' in result
        assert 'username' in result
        assert 'full_name' in result
        assert 'bio' in result
        assert 'avatar_url' in result
        assert 'created_at' in result
        
        # Sensitive fields should be excluded
        assert 'email' not in result
        assert 'updated_at' not in result
        assert 'last_login' not in result


class TestFormatProfileDisplay:
    """Test format_profile_display method."""
    
    def test_format_profile_display(self, user_profile, sample_user_data):
        """Test profile formatting for display."""
        result = user_profile.format_profile_display(sample_user_data)
        
        assert 'USER PROFILE' in result
        assert 'johndoe' in result
        assert 'john.doe@example.com' in result
        assert 'John Doe' in result
        assert 'Software developer' in result
        assert '=' * 50 in result
    
    def test_format_profile_display_with_missing_fields(self, user_profile):
        """Test profile formatting handles missing fields gracefully."""
        partial_data = {
            'id': 1,
            'username': 'testuser'
        }
        
        result = user_profile.format_profile_display(partial_data)
        
        assert 'testuser' in result
        assert 'N/A' in result  # Missing fields should show as N/A


class TestDatabaseConnection:
    """Test database connection functionality."""
    
    @patch('src.auth.profile.psycopg2.connect')
    def test_get_connection_success(self, mock_connect, user_profile):
        """Test successful database connection."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        conn = user_profile._get_connection()
        
        assert conn == mock_conn
        mock_connect.assert_called_once_with(user_profile.database_url)
    
    @patch('src.auth.profile.psycopg2.connect')
    def test_get_connection_failure(self, mock_connect, user_profile):
        """Test database connection failure."""
        import psycopg2
        mock_connect.side_effect = psycopg2.OperationalError("Connection refused")
        
        with pytest.raises(DatabaseConnectionError) as exc_info:
            user_profile._get_connection()
        
        assert "Failed to connect to database" in str(exc_info.value)
