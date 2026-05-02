"""
test_railway_router.py
======================
Unit tests for Railway router endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status
from fastapi.testclient import TestClient

from main import app
from railway_api import RailwayAPIError


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user."""
    return {"email": "test@example.com", "user_id": "123"}


@pytest.fixture
def mock_railway_client():
    """Mock Railway client."""
    client = AsyncMock()
    client.get_projects = AsyncMock()
    client.get_project_services = AsyncMock()
    client.get_project_environments = AsyncMock()
    client.get_service_deployments = AsyncMock()
    client.trigger_deployment = AsyncMock()
    client.get_deployment_status = AsyncMock()
    client.get_service_variables = AsyncMock()
    return client


class TestGetProjects:
    """Test GET /api/railway/projects endpoint."""
    
    def test_get_projects_success(self, client, mock_auth_user, mock_railway_client):
        """Test successful projects retrieval."""
        mock_projects = [
            {
                "id": "proj-1",
                "name": "Test Project",
                "description": "Test description",
                "createdAt": "2024-01-01T00:00:00Z"
            }
        ]
        mock_railway_client.get_projects.return_value = mock_projects
        
        with patch("railway_router.get_current_user", return_value=mock_auth_user):
            with patch("railway_router.get_railway_client", return_value=mock_railway_client):
                response = client.get("/api/railway/projects")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "proj-1"
        assert data[0]["name"] == "Test Project"
    
    def test_get_projects_unauthorized(self, client):
        """Test projects retrieval without authentication."""
        response = client.get("/api/railway/projects")
        # This should fail authentication
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    def test_get_projects_railway_error(self, client, mock_auth_user, mock_railway_client):
        """Test projects retrieval with Railway API error."""
        mock_railway_client.get_projects.side_effect = RailwayAPIError("API error")
        
        with patch("railway_router.get_current_user", return_value=mock_auth_user):
            with patch("railway_router.get_railway_client", return_value=mock_railway_client):
                response = client.get("/api/railway/projects")
        
        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        assert "Railway API error" in response.json()["detail"]


class TestGetProjectServices:
    """Test GET /api/railway/projects/{project_id}/services endpoint."""
    
    def test_get_services_success(self, client, mock_auth_user, mock_railway_client):
        """Test successful services retrieval."""
        mock_services = [
            {
                "id": "svc-1",
                "name": "API Service",
                "icon": "🚀",
                "createdAt": "2024-01-01T00:00:00Z"
            }
        ]
        mock_railway_client.get_project_services.return_value = mock_services
        
        with patch("railway_router.get_current_user", return_value=mock_auth_user):
            with patch("railway_router.get_railway_client", return_value=mock_railway_client):
                response = client.get("/api/railway/projects/proj-1/services")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "API Service"
    
    def test_get_services_railway_error(self, client, mock_auth_user, mock_railway_client):
        """Test services retrieval with Railway API error."""
        mock_railway_client.get_project_services.side_effect = RailwayAPIError(
            "Project not found"
        )
        
        with patch("railway_router.get_current_user", return_value=mock_auth_user):
            with patch("railway_router.get_railway_client", return_value=mock_railway_client):
                response = client.get("/api/railway/projects/invalid/services")
        
        assert response.status_code == status.HTTP_502_BAD_GATEWAY


class TestGetProjectEnvironments:
    """Test GET /api/railway/projects/{project_id}/environments endpoint."""
    
    def test_get_environments_success(self, client, mock_auth_user, mock_railway_client):
        """Test successful environments retrieval."""
        mock_envs = [
            {"id": "env-1", "name": "production", "createdAt": "2024-01-01T00:00:00Z"},
            {"id": "env-2", "name": "uat", "createdAt": "2024-01-02T00:00:00Z"}
        ]
        mock_railway_client.get_project_environments.return_value = mock_envs
        
        with patch("railway_router.get_current_user", return_value=mock_auth_user):
            with patch("railway_router.get_railway_client", return_value=mock_railway_client):
                response = client.get("/api/railway/projects/proj-1/environments")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "production"
        assert data[1]["name"] == "uat"


class TestGetServiceDeployments:
    """Test GET /api/railway/services/{service_id}/deployments endpoint."""
    
    def test_get_deployments_success(self, client, mock_auth_user, mock_railway_client):
        """Test successful deployments retrieval."""
        mock_deployments = [
            {
                "id": "dep-1",
                "status": "SUCCESS",
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-01T00:05:00Z",
                "staticUrl": "https://example.railway.app",
                "meta": {}
            }
        ]
        mock_railway_client.get_service_deployments.return_value = mock_deployments
        
        with patch("railway_router.get_current_user", return_value=mock_auth_user):
            with patch("railway_router.get_railway_client", return_value=mock_railway_client):
                response = client.get("/api/railway/services/svc-1/deployments?limit=5")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "SUCCESS"
        assert data[0]["static_url"] == "https://example.railway.app"


class TestTriggerDeployment:
    """Test POST /api/railway/deployments/trigger endpoint."""
    
    def test_trigger_deployment_success(self, client, mock_auth_user, mock_railway_client):
        """Test successful deployment trigger."""
        mock_deployment = {
            "id": "new-dep-1",
            "status": "QUEUED",
            "createdAt": "2024-01-01T00:00:00Z"
        }
        mock_railway_client.trigger_deployment.return_value = mock_deployment
        
        payload = {
            "service_id": "svc-1",
            "environment_id": "env-1"
        }
        
        with patch("railway_router.get_current_user", return_value=mock_auth_user):
            with patch("railway_router.get_railway_client", return_value=mock_railway_client):
                response = client.post("/api/railway/deployments/trigger", json=payload)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == "new-dep-1"
        assert data["status"] == "QUEUED"
        
        # Verify the trigger was called with correct parameters
        mock_railway_client.trigger_deployment.assert_called_once_with("svc-1", "env-1")
    
    def test_trigger_deployment_invalid_payload(self, client, mock_auth_user):
        """Test deployment trigger with invalid payload."""
        payload = {
            "service_id": "svc-1"
            # Missing environment_id
        }
        
        with patch("railway_router.get_current_user", return_value=mock_auth_user):
            response = client.post("/api/railway/deployments/trigger", json=payload)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_trigger_deployment_railway_error(
        self, client, mock_auth_user, mock_railway_client
    ):
        """Test deployment trigger with Railway API error."""
        mock_railway_client.trigger_deployment.side_effect = RailwayAPIError(
            "Service not found"
        )
        
        payload = {
            "service_id": "invalid",
            "environment_id": "env-1"
        }
        
        with patch("railway_router.get_current_user", return_value=mock_auth_user):
            with patch("railway_router.get_railway_client", return_value=mock_railway_client):
                response = client.post("/api/railway/deployments/trigger", json=payload)
        
        assert response.status_code == status.HTTP_502_BAD_GATEWAY


class TestGetDeploymentStatus:
    """Test GET /api/railway/deployments/{deployment_id} endpoint."""
    
    def test_get_deployment_status_success(
        self, client, mock_auth_user, mock_railway_client
    ):
        """Test successful deployment status retrieval."""
        mock_deployment = {
            "id": "dep-1",
            "status": "BUILDING",
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:02:00Z",
            "staticUrl": None,
            "meta": {}
        }
        mock_railway_client.get_deployment_status.return_value = mock_deployment
        
        with patch("railway_router.get_current_user", return_value=mock_auth_user):
            with patch("railway_router.get_railway_client", return_value=mock_railway_client):
                response = client.get("/api/railway/deployments/dep-1")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == "dep-1"
        assert data["status"] == "BUILDING"
    
    def test_get_deployment_status_not_found(
        self, client, mock_auth_user, mock_railway_client
    ):
        """Test deployment status for non-existent deployment."""
        mock_railway_client.get_deployment_status.side_effect = RailwayAPIError(
            "Deployment not found"
        )
        
        with patch("railway_router.get_current_user", return_value=mock_auth_user):
            with patch("railway_router.get_railway_client", return_value=mock_railway_client):
                response = client.get("/api/railway/deployments/invalid")
        
        assert response.status_code == status.HTTP_502_BAD_GATEWAY


class TestGetServiceVariables:
    """Test GET /api/railway/services/{service_id}/variables endpoint."""
    
    def test_get_variables_success(self, client, mock_auth_user, mock_railway_client):
        """Test successful variables retrieval."""
        mock_variables = {
            "DATABASE_URL": "postgres://...",
            "API_KEY": "***",
            "PORT": "8000"
        }
        mock_railway_client.get_service_variables.return_value = mock_variables
        
        with patch("railway_router.get_current_user", return_value=mock_auth_user):
            with patch("railway_router.get_railway_client", return_value=mock_railway_client):
                response = client.get(
                    "/api/railway/services/svc-1/variables?environment_id=env-1"
                )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "variables" in data
        assert data["variables"]["DATABASE_URL"] == "postgres://..."
        assert len(data["variables"]) == 3


class TestRailwayHealth:
    """Test GET /api/railway/health endpoint."""
    
    def test_health_with_token(self, client, monkeypatch):
        """Test health check with token configured."""
        monkeypatch.setenv("RAILWAY_API_TOKEN", "test-token")
        
        response = client.get("/api/railway/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_health_without_token(self, client, monkeypatch):
        """Test health check without token configured."""
        monkeypatch.delenv("RAILWAY_API_TOKEN", raising=False)
        
        response = client.get("/api/railway/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "unhealthy"
