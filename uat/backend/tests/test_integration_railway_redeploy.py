"""
test_integration_railway_redeploy.py
====================================
Integration tests for the /api/railway/redeploy endpoint.

Tests the full request-response cycle including authentication,
Railway API interaction, and error handling.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import logging


@pytest.fixture
def mock_railway_token(monkeypatch):
    """Mock Railway API token environment variable."""
    monkeypatch.setenv("RAILWAY_API_TOKEN", "test-railway-token-123")


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user."""
    return {
        "id": "user-123",
        "email": "test@example.com",
        "username": "testuser"
    }


@pytest.fixture
def app_client(mock_railway_token):
    """Create FastAPI test client with Railway router."""
    from main import app
    return TestClient(app)


@pytest.fixture
def mock_railway_client():
    """Create a mock Railway client."""
    mock_client = AsyncMock()
    return mock_client


class TestRedeployEndpointIntegration:
    """Integration tests for /api/railway/redeploy endpoint."""
    
    def test_redeploy_requires_authentication(self, app_client):
        """Test that redeploy endpoint requires authentication."""
        response = app_client.post(
            "/api/railway/redeploy",
            json={
                "service_id": "svc-123",
                "environment_id": "env-456"
            }
        )
        
        # Should return 401 Unauthorized without valid token
        assert response.status_code == 401
    
    def test_redeploy_successful_deployment(
        self, 
        app_client, 
        mock_railway_client,
        mock_auth_user,
        caplog
    ):
        """Test successful redeployment request."""
        # Mock Railway API response
        mock_deployment = {
            "id": "dep-789",
            "status": "QUEUED",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z",
            "staticUrl": None,
            "meta": {}
        }
        mock_railway_client.trigger_deployment.return_value = mock_deployment
        
        with patch("railway_router.get_railway_client", return_value=mock_railway_client):
            with patch("railway_router.get_current_user", return_value=mock_auth_user):
                with caplog.at_level(logging.INFO):
                    response = app_client.post(
                        "/api/railway/redeploy",
                        json={
                            "service_id": "svc-123",
                            "environment_id": "env-456"
                        }
                    )
        
        # Should return 200 OK with deployment info
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == "dep-789"
        assert data["status"] == "QUEUED"
        assert data["created_at"] == "2024-01-15T10:00:00Z"
        
        # Verify Railway client was called correctly
        mock_railway_client.trigger_deployment.assert_called_once_with(
            "svc-123",
            "env-456"
        )
        
        # Verify logging
        assert "triggered redeploy" in caplog.text
        assert "dep-789" in caplog.text
        assert "svc-123" in caplog.text
    
    def test_redeploy_invalid_service_id(
        self,
        app_client,
        mock_railway_client,
        mock_auth_user
    ):
        """Test redeployment with invalid service ID."""
        from railway_api import RailwayAPIError
        
        # Mock Railway API error
        mock_railway_client.trigger_deployment.side_effect = RailwayAPIError(
            "Service not found"
        )
        
        with patch("railway_router.get_railway_client", return_value=mock_railway_client):
            with patch("railway_router.get_current_user", return_value=mock_auth_user):
                response = app_client.post(
                    "/api/railway/redeploy",
                    json={
                        "service_id": "invalid-svc",
                        "environment_id": "env-456"
                    }
                )
        
        # Should return 502 Bad Gateway
        assert response.status_code == 502
        data = response.json()
        assert "Railway API error" in data["detail"]
    
    def test_redeploy_missing_required_fields(self, app_client, mock_auth_user):
        """Test redeployment with missing required fields."""
        with patch("railway_router.get_current_user", return_value=mock_auth_user):
            # Missing environment_id
            response = app_client.post(
                "/api/railway/redeploy",
                json={"service_id": "svc-123"}
            )
        
        # Should return 422 Unprocessable Entity
        assert response.status_code == 422
    
    def test_redeploy_empty_service_id(self, app_client, mock_auth_user):
        """Test redeployment with empty service_id."""
        with patch("railway_router.get_current_user", return_value=mock_auth_user):
            response = app_client.post(
                "/api/railway/redeploy",
                json={
                    "service_id": "",
                    "environment_id": "env-456"
                }
            )
        
        # Should return 422 Unprocessable Entity for validation error
        assert response.status_code == 422
    
    def test_redeploy_railway_api_connection_error(
        self,
        app_client,
        mock_railway_client,
        mock_auth_user,
        caplog
    ):
        """Test redeployment when Railway API is unreachable."""
        # Mock connection error
        mock_railway_client.trigger_deployment.side_effect = Exception(
            "Connection timeout"
        )
        
        with patch("railway_router.get_railway_client", return_value=mock_railway_client):
            with patch("railway_router.get_current_user", return_value=mock_auth_user):
                with caplog.at_level(logging.ERROR):
                    response = app_client.post(
                        "/api/railway/redeploy",
                        json={
                            "service_id": "svc-123",
                            "environment_id": "env-456"
                        }
                    )
        
        # Should return 500 Internal Server Error
        assert response.status_code == 500
        data = response.json()
        assert "Internal server error" in data["detail"]
        
        # Verify error was logged
        assert "Unexpected error during redeploy" in caplog.text
    
    def test_redeploy_with_complex_deployment_response(
        self,
        app_client,
        mock_railway_client,
        mock_auth_user
    ):
        """Test redeployment with full deployment response."""
        # Mock complete Railway API response
        mock_deployment = {
            "id": "dep-complex-123",
            "status": "BUILDING",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:05:00Z",
            "staticUrl": "https://service.railway.app",
            "meta": {
                "branch": "main",
                "commitHash": "abc123",
                "commitMessage": "Update deployment"
            }
        }
        mock_railway_client.trigger_deployment.return_value = mock_deployment
        
        with patch("railway_router.get_railway_client", return_value=mock_railway_client):
            with patch("railway_router.get_current_user", return_value=mock_auth_user):
                response = app_client.post(
                    "/api/railway/redeploy",
                    json={
                        "service_id": "svc-123",
                        "environment_id": "env-prod"
                    }
                )
        
        # Should return 200 OK with full deployment info
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == "dep-complex-123"
        assert data["status"] == "BUILDING"
        assert data["static_url"] == "https://service.railway.app"
        assert data["meta"] is not None
        assert data["meta"]["branch"] == "main"
    
    def test_redeploy_concurrent_requests(
        self,
        app_client,
        mock_railway_client,
        mock_auth_user
    ):
        """Test handling of concurrent redeploy requests."""
        # Mock different deployments for concurrent requests
        deployment_responses = [
            {
                "id": f"dep-{i}",
                "status": "QUEUED",
                "createdAt": f"2024-01-15T10:0{i}:00Z"
            }
            for i in range(3)
        ]
        
        mock_railway_client.trigger_deployment.side_effect = deployment_responses
        
        with patch("railway_router.get_railway_client", return_value=mock_railway_client):
            with patch("railway_router.get_current_user", return_value=mock_auth_user):
                responses = [
                    app_client.post(
                        "/api/railway/redeploy",
                        json={
                            "service_id": f"svc-{i}",
                            "environment_id": "env-456"
                        }
                    )
                    for i in range(3)
                ]
        
        # All requests should succeed
        for i, response in enumerate(responses):
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == f"dep-{i}"
            assert data["status"] == "QUEUED"
    
    def test_redeploy_request_validation(self, app_client, mock_auth_user):
        """Test request body validation."""
        with patch("railway_router.get_current_user", return_value=mock_auth_user):
            # Invalid JSON structure
            response = app_client.post(
                "/api/railway/redeploy",
                json={
                    "wrong_field": "value"
                }
            )
        
        # Should return 422 for validation error
        assert response.status_code == 422
    
    def test_redeploy_logs_user_action(
        self,
        app_client,
        mock_railway_client,
        mock_auth_user,
        caplog
    ):
        """Test that user actions are properly logged."""
        mock_deployment = {
            "id": "dep-log-test",
            "status": "QUEUED",
            "createdAt": "2024-01-15T10:00:00Z"
        }
        mock_railway_client.trigger_deployment.return_value = mock_deployment
        
        with patch("railway_router.get_railway_client", return_value=mock_railway_client):
            with patch("railway_router.get_current_user", return_value=mock_auth_user):
                with caplog.at_level(logging.INFO):
                    app_client.post(
                        "/api/railway/redeploy",
                        json={
                            "service_id": "svc-audit",
                            "environment_id": "env-prod"
                        }
                    )
        
        # Verify user email is logged
        assert "test@example.com" in caplog.text
        assert "triggered redeploy" in caplog.text
        assert "dep-log-test" in caplog.text
        assert "svc-audit" in caplog.text


class TestRedeployEndpointMiddleware:
    """Test redeploy endpoint with middleware integration."""
    
    def test_redeploy_adds_process_time_header(
        self,
        app_client,
        mock_railway_client,
        mock_auth_user
    ):
        """Test that middleware adds process time header."""
        mock_deployment = {
            "id": "dep-123",
            "status": "QUEUED",
            "createdAt": "2024-01-15T10:00:00Z"
        }
        mock_railway_client.trigger_deployment.return_value = mock_deployment
        
        with patch("railway_router.get_railway_client", return_value=mock_railway_client):
            with patch("railway_router.get_current_user", return_value=mock_auth_user):
                response = app_client.post(
                    "/api/railway/redeploy",
                    json={
                        "service_id": "svc-123",
                        "environment_id": "env-456"
                    }
                )
        
        # Should have process time header from middleware
        assert "X-Process-Time" in response.headers
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0
    
    def test_redeploy_request_logging(
        self,
        app_client,
        mock_railway_client,
        mock_auth_user,
        caplog
    ):
        """Test that request logging middleware logs redeploy requests."""
        mock_deployment = {
            "id": "dep-123",
            "status": "QUEUED",
            "createdAt": "2024-01-15T10:00:00Z"
        }
        mock_railway_client.trigger_deployment.return_value = mock_deployment
        
        with patch("railway_router.get_railway_client", return_value=mock_railway_client):
            with patch("railway_router.get_current_user", return_value=mock_auth_user):
                with caplog.at_level(logging.INFO):
                    app_client.post(
                        "/api/railway/redeploy",
                        json={
                            "service_id": "svc-123",
                            "environment_id": "env-456"
                        }
                    )
        
        # Verify request logging
        assert "Request started: POST /api/railway/redeploy" in caplog.text
        assert "Request completed: POST /api/railway/redeploy" in caplog.text


class TestRedeployEndpointResponseFormat:
    """Test response format and schema compliance."""
    
    def test_redeploy_response_schema(
        self,
        app_client,
        mock_railway_client,
        mock_auth_user
    ):
        """Test that response matches DeploymentStatusResponse schema."""
        mock_deployment = {
            "id": "dep-schema-test",
            "status": "SUCCESS",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:10:00Z",
            "staticUrl": "https://example.railway.app",
            "meta": {"key": "value"}
        }
        mock_railway_client.trigger_deployment.return_value = mock_deployment
        
        with patch("railway_router.get_railway_client", return_value=mock_railway_client):
            with patch("railway_router.get_current_user", return_value=mock_auth_user):
                response = app_client.post(
                    "/api/railway/redeploy",
                    json={
                        "service_id": "svc-123",
                        "environment_id": "env-456"
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields are present
        assert "id" in data
        assert "status" in data
        assert "created_at" in data
        
        # Verify optional fields
        assert "updated_at" in data
        assert "static_url" in data
        assert "meta" in data
        
        # Verify types
        assert isinstance(data["id"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["created_at"], str)
    
    def test_redeploy_response_with_null_fields(
        self,
        app_client,
        mock_railway_client,
        mock_auth_user
    ):
        """Test response handling with null optional fields."""
        mock_deployment = {
            "id": "dep-null-test",
            "status": "QUEUED",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": None,
            "staticUrl": None,
            "meta": None
        }
        mock_railway_client.trigger_deployment.return_value = mock_deployment
        
        with patch("railway_router.get_railway_client", return_value=mock_railway_client):
            with patch("railway_router.get_current_user", return_value=mock_auth_user):
                response = app_client.post(
                    "/api/railway/redeploy",
                    json={
                        "service_id": "svc-123",
                        "environment_id": "env-456"
                    }
                )
        
        assert response.status_code == 200
        data = response.json()
        
        # Null fields should be present but null
        assert data["updated_at"] is None
        assert data["static_url"] is None
        assert data["meta"] is None
