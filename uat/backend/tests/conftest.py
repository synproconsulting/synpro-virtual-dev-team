"""
backend/tests/conftest.py
Pytest configuration and shared fixtures for all tests.
"""

import pytest
import os
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def test_env():
    """Set up test environment variables."""
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["JWT_SECRET"] = "test-secret-key"
    os.environ["RATE_LIMIT_DEFAULT"] = "1000/minute"
    os.environ["RATE_LIMIT_STORAGE_URI"] = "memory://"
    os.environ["LOG_LEVEL"] = "DEBUG"
    yield


@pytest.fixture
def client(test_env):
    """Create a test client for the main application."""
    from main import app
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter between tests."""
    from rate_limiter import limiter
    # Clear any existing rate limit data
    if hasattr(limiter, '_storage'):
        limiter._storage.reset()
    yield
