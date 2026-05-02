"""
Shared pytest fixtures and configuration for backend tests.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add parent directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


@pytest.fixture
def mock_db():
    """
    Mock database connection fixture.
    
    Returns a tuple of (mock_connection, mock_cursor) that can be used
    to simulate database interactions in tests.
    
    Usage:
        def test_something(mock_db):
            mock_conn, mock_cursor = mock_db
            mock_cursor.fetchone.return_value = {"id": "test-id"}
            # ... rest of test
    """
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.commit = Mock()
    mock_conn.close = Mock()
    return mock_conn, mock_cursor


@pytest.fixture
def mock_db_connection(mock_db):
    """
    Mock database connection context manager.
    
    This fixture patches the get_db dependency to return a mocked
    database connection. Use this when you need to patch get_db
    at the module level.
    
    Usage:
        @pytest.fixture
        def client(mock_db_connection):
            from main import app
            return TestClient(app)
    """
    mock_conn, _ = mock_db
    
    def mock_get_db():
        yield mock_conn
    
    return mock_get_db


@pytest.fixture
def sample_user_data():
    """
    Sample user data for testing.
    
    Returns a dictionary with typical user fields.
    """
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "test@example.com",
        "username": "testuser",
        "password_hash": "fakehash:fakekey",
        "created_at": "2024-01-01T00:00:00+00:00"
    }


@pytest.fixture
def sample_reset_token_data():
    """
    Sample password reset token data for testing.
    
    Returns a dictionary with typical reset token fields.
    """
    from datetime import datetime, timezone, timedelta
    
    return {
        "id": "660e8400-e29b-41d4-a716-446655440000",
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "token": "770e8400-e29b-41d4-a716-446655440000",
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "used": False,
        "created_at": datetime.now(timezone.utc)
    }


@pytest.fixture(autouse=True)
def mock_environment():
    """
    Mock environment variables for testing.
    
    This fixture automatically runs for all tests and sets up
    safe default environment variables.
    """
    with patch.dict('os.environ', {
        'DATABASE_URL': 'postgresql://test:test@localhost/test',
        'JWT_SECRET': 'test-secret-key-minimum-32-characters-long-for-testing',
        'JWT_EXPIRY_HOURS': '24',
        'JWT_ALGORITHM': 'HS256',
        'CORS_ALLOWED_ORIGINS': 'http://localhost:3000',
        'SMTP_HOST': 'smtp.test.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': 'test@test.com',
        'SMTP_PASSWORD': 'testpass',
        'FRONTEND_URL': 'http://localhost:3000'
    }):
        yield
