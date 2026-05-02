"""
test_railway_router.py
======================
Integration tests for Railway deployment API endpoints.

Tests the /api/railway endpoints including deployment triggering (redeploy),
project/service listing, and deployment status queries.

SDT1-68: Add integration test for /api/railway/redeploy endpoint
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import os

from main import app
from railway_api import RailwayClient, RailwayAPIError


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_railway_client():
    """Mock RailwayClient for testing without actual API calls."""
    client = AsyncMock(spec=RailwayClient)
    
    # Mock successful responses
    client.get_projects.return_value = [
        {
            "id": "project-123",
            "name": "Test Project",
            "description": "A test project",
            "createdAt": "2024-01-01T00:00:00Z"
        }
    ]
    
    client.get_project_services.return_value = [
        {
            "id": "service-456",
            "name": "backend",
            "icon": "🚀",
            "createdAt": "2024-01-01T00:00:00Z"
        }
    ]
    
    client.get_project_environments.return_value = [
        {
            "id": "env-789",
            "name": "production",
            "createdAt": "2024-01-01T00:00:00Z"
        }
    ]
    
    client.get_service_deployments.return_value = [
        {
            "id": "deploy-001",
            "status": "SUCCESS",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:05:00Z",
            "staticUrl": "https://test.railway.app",
            "meta": {"commitHash": "abc123"}
        }
    ]
    
    client.trigger_deployment.return_value = {
        "id": "deploy-002",
        "status": "BUILDING",
        "createdAt": "2024-01-15T12:00:00Z"
    }
    
    client.get_deployment_status.return_value = {
        "id": "deploy-002",
        "status": "SUCCESS",
        "createdAt": "2024-01-15T12:00:00Z",
        "updatedAt": "2024-01-15T12:05:00Z",
        "staticUrl": "https://test.railway.app",
        "meta": {"commitHash": "def456"}
    }
    
    client.get_service_variables.return_value = {
        "DATABASE_URL": "postgresql://...",
        "API_KEY": "***"
    }
    
    return client


@pytest.fixture
def mock_auth_token():
    """Mock JWT token for authentication."""
    return "Bearer mock_token_12345"


@pytest.fixture
def mock_current_user():
    """Mock authenticated user."""
    return {
        "id": "user-123",
        "email": "test@example.com",
        "username": "testuser"
    }


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


# ── Health Check Tests ────────────────────────────────────────────────────────


def test_railway_health_with_token(client):
    """Test health endpoint when RAILWAY_API_TOKEN is configured."""
    with patch.dict(os.environ, {"RAILWAY_API_TOKEN": "test_token"}):
        response = client.get("/api/railway/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "Railway API configured" in data["message"]


def test_railway_health_without_token(client):
    """Test health endpoint when RAILWAY_API_TOKEN is not configured."""
    with patch.dict(os.environ, {}, clear=True):
        # Ensure RAILWAY_API_TOKEN is not set
        os.environ.pop("RAILWAY_API_TOKEN", None)
        response = client.get("/api/railway/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "not configured" in data["message"]


# ── Project Management Tests ──────────────────────────────────────────────────


def test_get_projects_success(client, mock_railway_client, mock_current_user, mock_auth_token):
    """Test successfully retrieving projects."""
    with patch("railway_router.get_railway_client", return_value=mock_railway_client), \
         patch("railway_router.get_current_user", return_value=mock_current_user):
        
        response = client.get(
            "/api/railway/projects",
            headers={"Authorization": mock_auth_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "project-123"
        assert data[0]["name"] == "Test Project"
        assert data[0]["description"] == "A test project"
        mock_railway_client.get_projects.assert_called_once()


def test_get_projects_unauthorized(client):
    """Test projects endpoint without authentication."""
    response = client.get("/api/railway/projects")
    assert response.status_code == 401


def test_get_projects_api_error(client, mock_railway_client, mock_current_user, mock_auth_token):
    """Test projects endpoint when Railway API fails."""
    mock_railway_client.get_projects.side_effect = RailwayAPIError("API connection failed")
    
    with patch("railway_router.get_railway_client", return_value=mock_railway_client), \
         patch("railway_router.get_current_user", return_value=mock_current_user):
        
        response = client.get(
            "/api/railway/projects",
            headers={"Authorization": mock_auth_token}
        )
        
        assert response.status_code == 502
        assert "Railway API error" in response.json()["detail"]


# ── Service Management Tests ──────────────────────────────────────────────────


def test_get_project_services_success(client, mock_railway_client, mock_current_user, mock_auth_token):
    """Test successfully retrieving services for a project."""
    with patch("railway_router.get_railway_client", return_value=mock_railway_client), \
         patch("railway_router.get_current_user", return_value=mock_current_user):
        
        response = client.get(
            "/api/railway/projects/project-123/services",
            headers={"Authorization": mock_auth_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "service-456"
        assert data[0]["name"] == "backend"
        assert data[0]["icon"] == "🚀"
        mock_railway_client.get_project_services.assert_called_once_with("project-123")


def test_get_project_services_unauthorized(client):
    """Test services endpoint without authentication."""
    response = client.get("/api/railway/projects/project-123/services")
    assert response.status_code == 401


# ── Environment Management Tests ──────────────────────────────────────────────


def test_get_project_environments_success(client, mock_railway_client, mock_current_user, mock_auth_token):
    """Test successfully retrieving environments for a project."""
    with patch("railway_router.get_railway_client", return_value=mock_railway_client), \
         patch("railway_router.get_current_user", return_value=mock_current_user):
        
        response = client.get(
            "/api/railway/projects/project-123/environments",
            headers={"Authorization": mock_auth_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "env-789"
        assert data[0]["name"] == "production"
        mock_railway_client.get_project_environments.assert_called_once_with("project-123")


# ── Deployment Management Tests ───────────────────────────────────────────────


def test_get_service_deployments_success(client, mock_railway_client, mock_current_user, mock_auth_token):
    """Test successfully retrieving deployments for a service."""
    with patch("railway_router.get_railway_client", return_value=mock_railway_client), \
         patch("railway_router.get_current_user", return_value=mock_current_user):
        
        response = client.get(
            "/api/railway/services/service-456/deployments",
            headers={"Authorization": mock_auth_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "deploy-001"
        assert data[0]["status"] == "SUCCESS"
        assert data[0]["static_url"] == "https://test.railway.app"
        mock_railway_client.get_service_deployments.assert_called_once_with("service-456", 10)


def test_get_service_deployments_with_limit(client, mock_railway_client, mock_current_user, mock_auth_token):
    """Test retrieving deployments with custom limit."""
    with patch("railway_router.get_railway_client", return_value=mock_railway_client), \
         patch("railway_router.get_current_user", return_value=mock_current_user):
        
        response = client.get(
            "/api/railway/services/service-456/deployments?limit=5",
            headers={"Authorization": mock_auth_token}
        )
        
        assert response.status_code == 200
        mock_railway_client.get_service_deployments.assert_called_once_with("service-456", 5)


# ── Deployment Trigger Tests (Redeploy) ───────────────────────────────────────


def test_trigger_deployment_success(client, mock_railway_client, mock_current_user, mock_auth_token):
    """
    Test successfully triggering a deployment (redeploy operation).
    
    SDT1-68: Integration test for /api/railway/redeploy endpoint.
    The /deployments/trigger endpoint performs a redeploy operation.
    """
    with patch("railway_router.get_railway_client", return_value=mock_railway_client), \
         patch("railway_router.get_current_user", return_value=mock_current_user):
        
        payload = {
            "service_id": "service-456",
            "environment_id": "env-789"
        }
        
        response = client.post(
            "/api/railway/deployments/trigger",
            json=payload,
            headers={"Authorization": mock_auth_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "deploy-002"
        assert data["status"] == "BUILDING"
        assert data["created_at"] == "2024-01-15T12:00:00Z"
        
        mock_railway_client.trigger_deployment.assert_called_once_with(
            "service-456",
            "env-789"
        )


def test_trigger_deployment_unauthorized(client):
    """Test deployment trigger without authentication."""
    payload = {
        "service_id": "service-456",
        "environment_id": "env-789"
    }
    
    response = client.post("/api/railway/deployments/trigger", json=payload)
    assert response.status_code == 401


def test_trigger_deployment_missing_fields(client, mock_current_user, mock_auth_token):
    """Test deployment trigger with missing required fields."""
    with patch("railway_router.get_current_user", return_value=mock_current_user):
        
        # Missing environment_id
        payload = {"service_id": "service-456"}
        response = client.post(
            "/api/railway/deployments/trigger",
            json=payload,
            headers={"Authorization": mock_auth_token}
        )
        assert response.status_code == 422
        
        # Missing service_id
        payload = {"environment_id": "env-789"}
        response = client.post(
            "/api/railway/deployments/trigger",
            json=payload,
            headers={"Authorization": mock_auth_token}
        )
        assert response.status_code == 422


def test_trigger_deployment_api_error(client, mock_railway_client, mock_current_user, mock_auth_token):
    """Test deployment trigger when Railway API fails."""
    mock_railway_client.trigger_deployment.side_effect = RailwayAPIError("Deployment failed")
    
    with patch("railway_router.get_railway_client", return_value=mock_railway_client), \
         patch("railway_router.get_current_user", return_value=mock_current_user):
        
        payload = {
            "service_id": "service-456",
            "environment_id": "env-789"
        }
        
        response = client.post(
            "/api/railway/deployments/trigger",
            json=payload,
            headers={"Authorization": mock_auth_token}
        )
        
        assert response.status_code == 502
        assert "Railway API error" in response.json()["detail"]


def test_trigger_deployment_unexpected_error(client, mock_railway_client, mock_current_user, mock_auth_token):
    """Test deployment trigger with unexpected error."""
    mock_railway_client.trigger_deployment.side_effect = Exception("Unexpected error")
    
    with patch("railway_router.get_railway_client", return_value=mock_railway_client), \
         patch("railway_router.get_current_user", return_value=mock_current_user):
        
        payload = {
            "service_id": "service-456",
            "environment_id": "env-789"
        }
        
        response = client.post(
            "/api/railway/deployments/trigger",
            json=payload,
            headers={"Authorization": mock_auth_token}
        )
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


# ── Deployment Status Tests ───────────────────────────────────────────────────


def test_get_deployment_status_success(client, mock_railway_client, mock_current_user, mock_auth_token):
    """Test successfully retrieving deployment status."""
    with patch("railway_router.get_railway_client", return_value=mock_railway_client), \
         patch("railway_router.get_current_user", return_value=mock_current_user):
        
        response = client.get(
            "/api/railway/deployments/deploy-002",
            headers={"Authorization": mock_auth_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "deploy-002"
        assert data["status"] == "SUCCESS"
        assert data["static_url"] == "https://test.railway.app"
        mock_railway_client.get_deployment_status.assert_called_once_with("deploy-002")


def test_get_deployment_status_not_found(client, mock_railway_client, mock_current_user, mock_auth_token):
    """Test retrieving status for non-existent deployment."""
    mock_railway_client.get_deployment_status.side_effect = RailwayAPIError(
        "Deployment not found"
    )
    
    with patch("railway_router.get_railway_client", return_value=mock_railway_client), \
         patch("railway_router.get_current_user", return_value=mock_current_user):
        
        response = client.get(
            "/api/railway/deployments/nonexistent",
            headers={"Authorization": mock_auth_token}
        )
        
        assert response.status_code == 502


# ── Service Variables Tests ───────────────────────────────────────────────────


def test_get_service_variables_success(client, mock_railway_client, mock_current_user, mock_auth_token):
    """Test successfully retrieving service environment variables."""
    with patch("railway_router.get_railway_client", return_value=mock_railway_client), \
         patch("railway_router.get_current_user", return_value=mock_current_user):
        
        response = client.get(
            "/api/railway/services/service-456/variables?environment_id=env-789",
            headers={"Authorization": mock_auth_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "variables" in data
        assert "DATABASE_URL" in data["variables"]
        assert "API_KEY" in data["variables"]
        mock_railway_client.get_service_variables.assert_called_once_with(
            "service-456",
            "env-789"
        )


def test_get_service_variables_missing_environment(client, mock_current_user, mock_auth_token):
    """Test retrieving variables without environment_id parameter."""
    with patch("railway_router.get_current_user", return_value=mock_current_user):
        
        response = client.get(
            "/api/railway/services/service-456/variables",
            headers={"Authorization": mock_auth_token}
        )
        
        # Should fail validation due to missing required query parameter
        assert response.status_code == 422


# ── Integration Test: Full Deployment Workflow ────────────────────────────────


def test_full_deployment_workflow(client, mock_railway_client, mock_current_user, mock_auth_token):
    """
    Integration test for complete deployment workflow.
    
    Tests the full flow: list projects -> list services -> trigger deployment -> check status.
    SDT1-68: Comprehensive test including redeploy operation.
    """
    with patch("railway_router.get_railway_client", return_value=mock_railway_client), \
         patch("railway_router.get_current_user", return_value=mock_current_user):
        
        # Step 1: Get projects
        response = client.get(
            "/api/railway/projects",
            headers={"Authorization": mock_auth_token}
        )
        assert response.status_code == 200
        projects = response.json()
        project_id = projects[0]["id"]
        
        # Step 2: Get services for project
        response = client.get(
            f"/api/railway/projects/{project_id}/services",
            headers={"Authorization": mock_auth_token}
        )
        assert response.status_code == 200
        services = response.json()
        service_id = services[0]["id"]
        
        # Step 3: Get environments for project
        response = client.get(
            f"/api/railway/projects/{project_id}/environments",
            headers={"Authorization": mock_auth_token}
        )
        assert response.status_code == 200
        environments = response.json()
        environment_id = environments[0]["id"]
        
        # Step 4: Trigger deployment (redeploy)
        payload = {
            "service_id": service_id,
            "environment_id": environment_id
        }
        response = client.post(
            "/api/railway/deployments/trigger",
            json=payload,
            headers={"Authorization": mock_auth_token}
        )
        assert response.status_code == 200
        deployment = response.json()
        deployment_id = deployment["id"]
        assert deployment["status"] == "BUILDING"
        
        # Step 5: Check deployment status
        response = client.get(
            f"/api/railway/deployments/{deployment_id}",
            headers={"Authorization": mock_auth_token}
        )
        assert response.status_code == 200
        status = response.json()
        assert status["id"] == deployment_id
        assert status["status"] == "SUCCESS"
        
        # Verify all mocks were called
        mock_railway_client.get_projects.assert_called()
        mock_railway_client.get_project_services.assert_called()
        mock_railway_client.get_project_environments.assert_called()
        mock_railway_client.trigger_deployment.assert_called()
        mock_railway_client.get_deployment_status.assert_called()
