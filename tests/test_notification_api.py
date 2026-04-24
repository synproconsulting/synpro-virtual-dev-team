"""
Unit tests for notification preferences API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import Mock, patch

from src.auth.notification_api import (
    router,
    get_notification_manager,
    get_current_user
)
from src.auth.notification_preferences import (
    NotificationPreferencesManager,
    NotificationType,
    EventCategory,
    NotificationPreferencesProfile
)


@pytest.fixture
def app():
    """Create a test FastAPI application."""
    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_manager():
    """Create a mock notification preferences manager."""
    return Mock(spec=NotificationPreferencesManager)


@pytest.fixture
def mock_user_id():
    """Return a mock user ID."""
    return "test_user_123"


def override_get_current_user(user_id: str):
    """Factory function to create a user dependency override."""
    def _get_user():
        return user_id
    return _get_user


def override_get_manager(manager: Mock):
    """Factory function to create a manager dependency override."""
    def _get_manager():
        return manager
    return _get_manager


class TestGetUserPreferences:
    """Test cases for GET /api/v1/notifications/preferences endpoint."""
    
    def test_get_user_preferences_success(self, app, client, mock_manager, mock_user_id):
        """Test successfully getting user preferences."""
        # Setup
        app.dependency_overrides[get_current_user] = override_get_current_user(mock_user_id)
        app.dependency_overrides[get_notification_manager] = override_get_manager(mock_manager)
        
        mock_profile = NotificationPreferencesProfile(
            user_id=mock_user_id,
            global_mute=False
        )
        mock_manager.get_user_preferences.return_value = mock_profile
        
        # Execute
        response = client.get("/api/v1/notifications/preferences")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['user_id'] == mock_user_id
        assert data['global_mute'] is False
        mock_manager.get_user_preferences.assert_called_once_with(mock_user_id)


class TestMetadataEndpoints:
    """Test cases for metadata endpoints."""
    
    def test_get_event_categories(self, client):
        """Test getting list of event categories."""
        response = client.get("/api/v1/notifications/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "security" in data
        assert "account" in data
        assert "marketing" in data
    
    def test_get_notification_types(self, client):
        """Test getting list of notification types."""
        response = client.get("/api/v1/notifications/types")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "email" in data
        assert "sms" in data
        assert "push" in data
        assert "in_app" in data
