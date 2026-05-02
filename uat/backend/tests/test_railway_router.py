"""
Tests for Railway API router endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app

client = TestClient(app)


class TestRailwayRouter:
    """Test suite for Railway API endpoints."""

    @patch("railway_router.get_railway_client")
    def test_get_projects_success(self, mock_get_client):
        """Test successful projects retrieval."""
        mock_client = AsyncMock()
        mock_client.get_projects.return_value = [
            {
                "id": "project1",
                "name": "Test Project",
                "description": "A test project"
            }
        ]
        mock_get_client.return_value = mock_client
        
        response = client.get("/api/railway/projects")
        
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert len(data["projects"]) == 1
        assert data["projects"][0]["name"] == "Test Project"

    @patch("railway_router.get_railway_client")
    def test_get_projects_not_configured(self, mock_get_client):
        """Test projects endpoint when Railway not configured."""
        mock_get_client.side_effect = ValueError("Railway API token is required")
        
        response = client.get("/api/railway/projects")
        
        assert response.status_code == 500
        assert "Railway API not configured" in response.json()["detail"]

    @patch("railway_router.get_railway_client")
    def test_get_projects_api_error(self, mock_get_client):
        """Test projects endpoint with API error."""
        mock_client = AsyncMock()
        mock_client.get_projects.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client
        
        response = client.get("/api/railway/projects")
        
        assert response.status_code == 500
        assert "Failed to fetch projects" in response.json()["detail"]

    @patch("railway_router.get_railway_client")
    def test_get_project_services_success(self, mock_get_client):
        """Test successful services retrieval."""
        mock_client = AsyncMock()
        mock_client.get_project_services.return_value = [
            {
                "id": "service1",
                "name": "API Service"
            }
        ]
        mock_get_client.return_value = mock_client
        
        response = client.get("/api/railway/projects/project1/services")
        
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert len(data["services"]) == 1
        assert data["services"][0]["name"] == "API Service"

    @patch("railway_router.get_railway_client")
    def test_get_service_deployments_success(self, mock_get_client):
        """Test successful deployments retrieval."""
        mock_client = AsyncMock()
        mock_client.get_service_deployments.return_value = [
            {
                "id": "deployment1",
                "status": "SUCCESS",
                "createdAt": "2024-01-01T00:00:00Z"
            }
        ]
        mock_get_client.return_value = mock_client
        
        response = client.get("/api/railway/services/service1/deployments")
        
        assert response.status_code == 200
        data = response.json()
        assert "deployments" in data
        assert len(data["deployments"]) == 1
        assert data["deployments"][0]["status"] == "SUCCESS"

    @patch("railway_router.get_railway_client")
    def test_get_service_deployments_with_filters(self, mock_get_client):
        """Test deployments retrieval with query parameters."""
        mock_client = AsyncMock()
        mock_client.get_service_deployments.return_value = []
        mock_get_client.return_value = mock_client
        
        response = client.get(
            "/api/railway/services/service1/deployments"
            "?environment_id=env1&limit=5"
        )
        
        assert response.status_code == 200
        # Verify the client method was called with correct parameters
        mock_client.get_service_deployments.assert_called_once()
        call_kwargs = mock_client.get_service_deployments.call_args[1]
        assert call_kwargs["environment_id"] == "env1"
        assert call_kwargs["limit"] == 5

    @patch("railway_router.get_railway_client")
    def test_get_environment_deployments_success(self, mock_get_client):
        """Test successful environment deployments retrieval."""
        mock_client = AsyncMock()
        mock_client.get_environment_deployments.return_value = [
            {
                "id": "deployment1",
                "status": "SUCCESS",
                "serviceName": "API Service"
            }
        ]
        mock_get_client.return_value = mock_client
        
        response = client.get(
            "/api/railway/projects/project1/environments/production/deployments"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["environment"] == "production"
        assert len(data["deployments"]) == 1
        assert data["deployments"][0]["serviceName"] == "API Service"

    @patch("railway_router.get_railway_client")
    def test_get_deployment_logs_success(self, mock_get_client):
        """Test successful deployment logs retrieval."""
        mock_client = AsyncMock()
        mock_client.get_deployment_logs.return_value = [
            {
                "id": "log1",
                "message": "Deployment started",
                "timestamp": "2024-01-01T00:00:00Z",
                "severity": "INFO"
            }
        ]
        mock_get_client.return_value = mock_client
        
        response = client.get("/api/railway/deployments/deployment1/logs")
        
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert len(data["logs"]) == 1
        assert data["logs"][0]["message"] == "Deployment started"

    @patch("railway_router.get_railway_client")
    def test_trigger_deployment_success(self, mock_get_client):
        """Test successful deployment trigger."""
        mock_client = AsyncMock()
        mock_client.trigger_deployment.return_value = {
            "id": "deployment1",
            "status": "INITIALIZING",
            "createdAt": "2024-01-01T00:00:00Z"
        }
        mock_get_client.return_value = mock_client
        
        response = client.post(
            "/api/railway/deployments/trigger",
            json={
                "service_id": "service1",
                "environment_id": "env1"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["deployment"]["id"] == "deployment1"
        assert "message" in data

    @patch("railway_router.get_railway_client")
    def test_trigger_deployment_invalid_payload(self, mock_get_client):
        """Test deployment trigger with invalid payload."""
        response = client.post(
            "/api/railway/deployments/trigger",
            json={
                "service_id": "service1"
                # Missing environment_id
            }
        )
        
        assert response.status_code == 422  # Validation error

    @patch("railway_router.get_railway_client")
    def test_trigger_deployment_api_error(self, mock_get_client):
        """Test deployment trigger with API error."""
        mock_client = AsyncMock()
        mock_client.trigger_deployment.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client
        
        response = client.post(
            "/api/railway/deployments/trigger",
            json={
                "service_id": "service1",
                "environment_id": "env1"
            }
        )
        
        assert response.status_code == 500
        assert "Failed to trigger deployment" in response.json()["detail"]

    @patch("railway_router.get_railway_client")
    def test_railway_health_check_healthy(self, mock_get_client):
        """Test health check when Railway is configured and accessible."""
        mock_client = AsyncMock()
        mock_client.get_projects.return_value = [
            {"id": "project1", "name": "Test"}
        ]
        mock_get_client.return_value = mock_client
        
        response = client.get("/api/railway/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["configured"] is True
        assert data["projects_count"] == 1

    @patch("railway_router.get_railway_client")
    def test_railway_health_check_unconfigured(self, mock_get_client):
        """Test health check when Railway is not configured."""
        mock_get_client.side_effect = ValueError("Token required")
        
        response = client.get("/api/railway/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unconfigured"
        assert data["configured"] is False

    @patch("railway_router.get_railway_client")
    def test_railway_health_check_unhealthy(self, mock_get_client):
        """Test health check when Railway is configured but not accessible."""
        mock_client = AsyncMock()
        mock_client.get_projects.side_effect = Exception("Network error")
        mock_get_client.return_value = mock_client
        
        response = client.get("/api/railway/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["configured"] is True
        assert "error" in data
