"""
Tests for deployment router.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

from main import app
from railway_client import RailwayClient, RailwayClientError, RailwayService, RailwayDeployment


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_auth():
    """Mock authentication dependency."""
    with patch('deployment_router.get_current_user') as mock:
        mock.return_value = {"email": "test@example.com", "user_id": "123"}
        yield mock


@pytest.fixture
def mock_railway_client():
    """Mock Railway client dependency."""
    mock_client = MagicMock(spec=RailwayClient)
    
    with patch('deployment_router.get_railway_client') as mock:
        mock.return_value = mock_client
        yield mock_client


class TestListServices:
    """Tests for listing services endpoint."""

    def test_list_services_success(self, client, mock_auth, mock_railway_client):
        """Test successful service listing."""
        mock_railway_client.list_services = AsyncMock(return_value=[
            RailwayService(
                id="service-1",
                name="API Service",
                icon="🚀",
                created_at="2024-01-01T00:00:00Z",
            ),
            RailwayService(
                id="service-2",
                name="Frontend",
                icon="⚛️",
                created_at="2024-01-01T00:00:00Z",
            ),
        ])
        
        response = client.get("/api/deployments/services")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "API Service"
        assert data[1]["name"] == "Frontend"

    def test_list_services_error(self, client, mock_auth, mock_railway_client):
        """Test service listing with Railway error."""
        mock_railway_client.list_services = AsyncMock(
            side_effect=RailwayClientError("API error")
        )
        
        response = client.get("/api/deployments/services")
        assert response.status_code == 500
        assert "API error" in response.json()["detail"]


class TestListEnvironments:
    """Tests for listing environments endpoint."""

    def test_list_environments_success(self, client, mock_auth, mock_railway_client):
        """Test successful environment listing."""
        from railway_client import RailwayEnvironment
        
        mock_railway_client.list_environments = AsyncMock(return_value=[
            RailwayEnvironment(
                id="env-1",
                name="UAT",
                service_instances=[],
            ),
            RailwayEnvironment(
                id="env-2",
                name="Production",
                service_instances=[],
            ),
        ])
        
        response = client.get("/api/deployments/environments")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "UAT"
        assert data[1]["name"] == "Production"


class TestTriggerDeployment:
    """Tests for trigger deployment endpoint."""

    def test_trigger_deployment_success(self, client, mock_auth, mock_railway_client):
        """Test successful deployment trigger."""
        mock_railway_client.trigger_deployment = AsyncMock(return_value="deployment-123")
        mock_railway_client.get_deployment_status = AsyncMock(return_value=RailwayDeployment(
            id="deployment-123",
            status="BUILDING",
            environment_name="UAT",
            service_name="API Service",
            created_at="2024-01-01T12:00:00Z",
            url="https://api.example.com",
        ))
        
        payload = {
            "service_ids": ["service-1"],
            "environment_id": "env-1",
            "deployment_notes": "Test deployment",
        }
        
        response = client.post("/api/deployments/trigger", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert len(data["deployments"]) == 1
        assert data["deployments"][0]["id"] == "deployment-123"

    def test_trigger_deployment_multiple_services(self, client, mock_auth, mock_railway_client):
        """Test deployment trigger for multiple services."""
        def mock_trigger(service_id, environment_id=None):
            return f"deployment-{service_id}"
        
        def mock_status(deployment_id):
            service_id = deployment_id.split('-')[1]
            return RailwayDeployment(
                id=deployment_id,
                status="BUILDING",
                environment_name="UAT",
                service_name=f"Service {service_id}",
                created_at="2024-01-01T12:00:00Z",
            )
        
        mock_railway_client.trigger_deployment = AsyncMock(side_effect=mock_trigger)
        mock_railway_client.get_deployment_status = AsyncMock(side_effect=mock_status)
        
        payload = {
            "service_ids": ["service-1", "service-2", "service-3"],
        }
        
        response = client.post("/api/deployments/trigger", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert len(data["deployments"]) == 3

    def test_trigger_deployment_no_services(self, client, mock_auth, mock_railway_client):
        """Test deployment trigger without service IDs."""
        payload = {"service_ids": []}
        
        response = client.post("/api/deployments/trigger", json=payload)
        assert response.status_code == 400
        assert "at least one service" in response.json()["detail"].lower()

    def test_trigger_deployment_partial_failure(self, client, mock_auth, mock_railway_client):
        """Test deployment trigger with some failures."""
        def mock_trigger(service_id, environment_id=None):
            if service_id == "service-2":
                raise RailwayClientError("Service not found")
            return f"deployment-{service_id}"
        
        def mock_status(deployment_id):
            return RailwayDeployment(
                id=deployment_id,
                status="BUILDING",
                environment_name="UAT",
                service_name="API Service",
                created_at="2024-01-01T12:00:00Z",
            )
        
        mock_railway_client.trigger_deployment = AsyncMock(side_effect=mock_trigger)
        mock_railway_client.get_deployment_status = AsyncMock(side_effect=mock_status)
        
        payload = {"service_ids": ["service-1", "service-2"]}
        
        response = client.post("/api/deployments/trigger", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert len(data["deployments"]) == 1
        assert len(data["failed_services"]) == 1
        assert data["failed_services"][0]["service_id"] == "service-2"

    def test_trigger_deployment_all_failures(self, client, mock_auth, mock_railway_client):
        """Test deployment trigger where all services fail."""
        mock_railway_client.trigger_deployment = AsyncMock(
            side_effect=RailwayClientError("All services failed")
        )
        
        payload = {"service_ids": ["service-1"]}
        
        response = client.post("/api/deployments/trigger", json=payload)
        assert response.status_code == 500


class TestGetDeploymentStatus:
    """Tests for get deployment status endpoint."""

    def test_get_status_success(self, client, mock_auth, mock_railway_client):
        """Test successful status retrieval."""
        mock_railway_client.get_deployment_status = AsyncMock(return_value=RailwayDeployment(
            id="deployment-123",
            status="SUCCESS",
            environment_name="UAT",
            service_name="API Service",
            created_at="2024-01-01T12:00:00Z",
            url="https://api.example.com",
        ))
        
        response = client.get("/api/deployments/status/deployment-123")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == "deployment-123"
        assert data["status"] == "SUCCESS"

    def test_get_status_not_found(self, client, mock_auth, mock_railway_client):
        """Test status retrieval for non-existent deployment."""
        mock_railway_client.get_deployment_status = AsyncMock(
            side_effect=RailwayClientError("Deployment not found")
        )
        
        response = client.get("/api/deployments/status/nonexistent")
        assert response.status_code == 404


class TestGetDeploymentHistory:
    """Tests for get deployment history endpoint."""

    def test_get_history_success(self, client, mock_auth, mock_railway_client):
        """Test successful history retrieval."""
        mock_railway_client.list_deployments = AsyncMock(return_value=[
            RailwayDeployment(
                id="deployment-1",
                status="SUCCESS",
                environment_name="UAT",
                service_name="API Service",
                created_at="2024-01-01T12:00:00Z",
            ),
            RailwayDeployment(
                id="deployment-2",
                status="FAILED",
                environment_name="UAT",
                service_name="Frontend",
                created_at="2024-01-01T11:00:00Z",
            ),
        ])
        
        response = client.get("/api/deployments/history")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 2
        assert len(data["deployments"]) == 2

    def test_get_history_with_filters(self, client, mock_auth, mock_railway_client):
        """Test history retrieval with filters."""
        mock_railway_client.list_deployments = AsyncMock(return_value=[
            RailwayDeployment(
                id="deployment-1",
                status="SUCCESS",
                environment_name="UAT",
                service_name="API Service",
                created_at="2024-01-01T12:00:00Z",
            ),
        ])
        
        response = client.get("/api/deployments/history?service_id=service-1&limit=5")
        assert response.status_code == 200
        
        # Verify the mock was called with correct parameters
        mock_railway_client.list_deployments.assert_called_once()
        call_args = mock_railway_client.list_deployments.call_args
        assert call_args.kwargs["service_id"] == "service-1"
        assert call_args.kwargs["limit"] == 5


class TestGetDeploymentLogs:
    """Tests for get deployment logs endpoint."""

    def test_get_logs_success(self, client, mock_auth, mock_railway_client):
        """Test successful log retrieval."""
        mock_railway_client.get_service_logs = AsyncMock(return_value=[
            "Starting deployment...",
            "Building image...",
            "Deployment complete!",
        ])
        
        response = client.get("/api/deployments/logs/deployment-123")
        assert response.status_code == 200
        
        data = response.json()
        assert data["deployment_id"] == "deployment-123"
        assert len(data["logs"]) == 3
        assert data["total"] == 3

    def test_get_logs_with_limit(self, client, mock_auth, mock_railway_client):
        """Test log retrieval with limit."""
        mock_railway_client.get_service_logs = AsyncMock(return_value=[
            "Log line 1",
            "Log line 2",
        ])
        
        response = client.get("/api/deployments/logs/deployment-123?limit=50")
        assert response.status_code == 200
        
        # Verify the mock was called with correct limit
        mock_railway_client.get_service_logs.assert_called_once()
        call_args = mock_railway_client.get_service_logs.call_args
        assert call_args.kwargs["limit"] == 50

    def test_get_logs_error(self, client, mock_auth, mock_railway_client):
        """Test log retrieval with error."""
        mock_railway_client.get_service_logs = AsyncMock(
            side_effect=RailwayClientError("Failed to fetch logs")
        )
        
        response = client.get("/api/deployments/logs/deployment-123")
        assert response.status_code == 500
