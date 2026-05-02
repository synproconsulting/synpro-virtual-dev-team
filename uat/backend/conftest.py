"""
conftest.py
===========
Pytest configuration and shared fixtures for backend tests.

Provides common test fixtures and setup for all test modules.
"""

import pytest
import os
from unittest.mock import patch


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Set up test environment variables for all tests.
    
    This runs once per test session and ensures necessary
    environment variables are set for testing.
    """
    # Set up minimal required environment variables for testing
    test_env = {
        "JWT_SECRET": "test_secret_key_at_least_32_characters_long_for_testing",
        "JWT_EXPIRY_HOURS": "24",
        "RAILWAY_API_TOKEN": "test_railway_token",
        "CORS_ALLOWED_ORIGINS": "http://localhost:3000,http://localhost:5173",
        "ENVIRONMENT": "test",
        "LOG_LEVEL": "INFO",
    }
    
    with patch.dict(os.environ, test_env, clear=False):
        yield


@pytest.fixture
def mock_db_connection():
    """Mock database connection for tests that need it."""
    from unittest.mock import MagicMock
    
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    return mock_conn, mock_cursor


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "test-user-123",
        "email": "test@example.com",
        "username": "testuser",
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_jwt_token():
    """Sample JWT token for authentication testing."""
    return "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItMTIzIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIn0.test_signature"


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
