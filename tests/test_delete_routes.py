"""
Unit tests for user deletion API routes.

Tests the UserDeletionRoutes class and route handlers for proper
request handling, authorization, and response formatting.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from src.auth.delete_routes import (
    DeleteUserRequest,
    DeleteUserResponse,
    UserDeletionRoutes,
    create_deletion_routes
)
from src.auth.delete_user import (
    UserDeletionService,
    UnauthorizedDeletionError,
    UserNotFoundError
)


class TestDeleteUserRequest:
    """Test suite for DeleteUserRequest model."""
    
    def test_initialization_minimal(self):
        """Test request initialization with minimal parameters."""
        request = DeleteUserRequest(user_id="user123")
        
        assert request.user_id == "user123"
        assert request.force_hard_delete is False
        assert request.confirmation_token is None
    
    def test_initialization_complete(self):
        """Test request initialization with all parameters."""
        request = DeleteUserRequest(
            user_id="user123",
            force_hard_delete=True,
            confirmation_token="token123"
        )
        
        assert request.user_id == "user123"
        assert request.force_hard_delete is True
        assert request.confirmation_token == "token123"


class TestDeleteUserResponse:
    """Test suite for DeleteUserResponse model."""
    
    def test_initialization(self):
        """Test response initialization."""
        response = DeleteUserResponse(
            success=True,
            user_id="user123",
            deletion_type="soft",
            deleted_at="2024-01-01T00:00:00",
            message="Account deleted"
        )
        
        assert response.success is True
        assert response.user_id == "user123"
        assert response.deletion_type == "soft"
        assert response.deleted_at == "2024-01-01T00:00:00"
        assert response.message == "Account deleted"
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        response = DeleteUserResponse(
            success=True,
            user_id="user123",
            deletion_type="hard",
            deleted_at="2024-01-01T00:00:00",
            message="Account deleted"
        )
        
        result = response.to_dict()
        
        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["user_id"] == "user123"
        assert result["deletion_type"] == "hard"
        assert result["deleted_at"] == "2024-01-01T00:00:00"
        assert result["message"] == "Account deleted"


class TestUserDeletionRoutes:
    """Test suite for UserDeletionRoutes class."""
    
    @pytest.fixture
    def mock_deletion_service(self):
        """Fixture providing a mock deletion service."""
        service = Mock(spec=UserDeletionService)
        return service
    
    @pytest.fixture
    def routes(self, mock_deletion_service):
        """Fixture providing routes handler."""
        return UserDeletionRoutes(mock_deletion_service)
    
    def test_initialization(self, mock_deletion_service):
        """Test routes handler initialization."""
        routes = UserDeletionRoutes(mock_deletion_service)
        assert routes.deletion_service is mock_deletion_service
    
    def test_delete_current_user_success(self, routes, mock_deletion_service):
        """Test successful deletion of current user."""
        mock_deletion_service.delete_user.return_value = {
            "success": True,
            "user_id": "user123",
            "deletion_type": "soft",
            "deleted_at": "2024-01-01T00:00:00"
        }
        
        # Mock confirmation verification
        routes._verify_confirmation = Mock(return_value=True)
        
        result = routes.delete_current_user(
            current_user_id="user123",
            confirmation_token="confirm_delete_user123"
        )
        
        assert result["success"] is True
        assert result["user_id"] == "user123"
        assert result["status_code"] == 200
        assert "deleted" in result["message"].lower()
        
        mock_deletion_service.delete_user.assert_called_once_with(
            user_id="user123",
            requesting_user_id="user123",
            force_hard_delete=False
        )


class TestCreateDeletionRoutes:
    """Test suite for create_deletion_routes factory function."""
    
    def test_create_deletion_routes(self):
        """Test factory function creates routes handler."""
        mock_service = Mock(spec=UserDeletionService)
        
        routes = create_deletion_routes(mock_service)
        
        assert isinstance(routes, UserDeletionRoutes)
        assert routes.deletion_service is mock_service
