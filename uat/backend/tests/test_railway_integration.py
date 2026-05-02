"""
Integration tests for Railway GraphQL API end-to-end flow.

These tests verify the complete integration between the frontend API client,
backend router, and Railway GraphQL client.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, Mock
from main import app

client = TestClient(app)


class TestRailwayIntegration:
    """
    Integration test suite for Railway deployment monitoring.
    
    These tests simulate real-world usage scenarios of the UAT Deploy tab.
    """

    @patch("railway_router.get_railway_client")
    def test_complete_deployment_monitoring_flow(self, mock_get_client):
        """
        Test the complete flow: projects → services → deployments.
        
        This simulates a user:
        1. Loading the UAT Deploy tab
        2. Fetching available projects
        3. Selecting a project and viewing its services
        4. Viewing deployments for a specific environment
        """
        # Setup mock Railway client
        mock_client = AsyncMock()
        
        # Mock projects response
        mock_client.get_projects.return_value = [
            {
                "id": "project-123",
                "name": "UAT Environment",
                "description": "Production UAT environment",
                "createdAt": "2024-01-01T00:00:00Z"
            }
        ]
        
        # Mock services response
        mock_client.get_project_services.return_value = [
            {
                "id": "service-api",
                "name": "auth-api",
                "createdAt": "2024-01-01T00:00:00Z"
            },
            {
                "id": "service-frontend",
                "name": "control-centre",
                "createdAt": "2024-01-01T00:00:00Z"
            }
        ]
        
        # Mock environment deployments response
        mock_client.get_environment_deployments.return_value = [
            {
                "id": "deploy-1",
                "status": "SUCCESS",
                "createdAt": "2024-01-15T10:00:00Z",
                "updatedAt": "2024-01-15T10:05:00Z",
                "staticUrl": "https://auth-api-production.railway.app",
                "serviceId": "service-api",
                "serviceName": "auth-api"
            },
            {
                "id": "deploy-2",
                "status": "BUILDING",
                "createdAt": "2024-01-15T10:10:00Z",
                "updatedAt": "2024-01-15T10:12:00Z",
                "staticUrl": "https://control-centre-production.railway.app",
                "serviceId": "service-frontend",
                "serviceName": "control-centre"
            }
        ]
        
        mock_get_client.return_value = mock_client
        
        # Step 1: User opens UAT Deploy tab - load projects
        projects_response = client.get("/api/railway/projects")
        assert projects_response.status_code == 200
        projects_data = projects_response.json()
        assert len(projects_data["projects"]) == 1
        assert projects_data["projects"][0]["name"] == "UAT Environment"
        
        project_id = projects_data["projects"][0]["id"]
        
        # Step 2: User selects project - load services
        services_response = client.get(f"/api/railway/projects/{project_id}/services")
        assert services_response.status_code == 200
        services_data = services_response.json()
        assert len(services_data["services"]) == 2
        assert services_data["services"][0]["name"] == "auth-api"
        
        # Step 3: User selects environment - load deployments
        deployments_response = client.get(
            f"/api/railway/projects/{project_id}/environments/production/deployments"
        )
        assert deployments_response.status_code == 200
        deployments_data = deployments_response.json()
        assert deployments_data["environment"] == "production"
        assert len(deployments_data["deployments"]) == 2
        
        # Verify deployment details
        api_deployment = deployments_data["deployments"][0]
        assert api_deployment["serviceName"] == "auth-api"
        assert api_deployment["status"] == "SUCCESS"
        assert "staticUrl" in api_deployment
        
        frontend_deployment = deployments_data["deployments"][1]
        assert frontend_deployment["serviceName"] == "control-centre"
        assert frontend_deployment["status"] == "BUILDING"

    @patch("railway_router.get_railway_client")
    def test_health_check_and_error_recovery(self, mock_get_client):
        """
        Test health check and graceful error handling.
        
        Simulates:
        1. Initial health check (healthy)
        2. API error during operation
        3. Health check detecting the issue
        """
        mock_client = AsyncMock()
        
        # Initial health check - healthy
        mock_client.get_projects.return_value = [
            {"id": "project-1", "name": "Test Project"}
        ]
        mock_get_client.return_value = mock_client
        
        health_response = client.get("/api/railway/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "healthy"
        assert health_data["configured"] is True
        
        # Simulate API error
        mock_client.get_projects.side_effect = Exception("Network error")
        
        # Attempt to fetch projects - should fail gracefully
        projects_response = client.get("/api/railway/projects")
        assert projects_response.status_code == 500
        assert "Failed to fetch projects" in projects_response.json()["detail"]
        
        # Health check should detect the issue
        health_response = client.get("/api/railway/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "unhealthy"
        assert "error" in health_data

    @patch("railway_router.get_railway_client")
    def test_multi_environment_comparison(self, mock_get_client):
        """
        Test viewing deployments across multiple environments.
        
        This is useful for comparing deployment status between staging and production.
        """
        mock_client = AsyncMock()
        
        # Mock production deployments
        production_deployments = [
            {
                "id": "prod-deploy-1",
                "status": "SUCCESS",
                "createdAt": "2024-01-15T09:00:00Z",
                "serviceName": "auth-api"
            }
        ]
        
        # Mock staging deployments
        staging_deployments = [
            {
                "id": "staging-deploy-1",
                "status": "BUILDING",
                "createdAt": "2024-01-15T10:00:00Z",
                "serviceName": "auth-api"
            }
        ]
        
        # Configure mock to return different data based on environment
        def get_env_deployments(project_id, environment_name):
            if environment_name == "production":
                return production_deployments
            elif environment_name == "staging":
                return staging_deployments
            return []
        
        mock_client.get_environment_deployments.side_effect = get_env_deployments
        mock_get_client.return_value = mock_client
        
        # Fetch production deployments
        prod_response = client.get(
            "/api/railway/projects/project-1/environments/production/deployments"
        )
        assert prod_response.status_code == 200
        prod_data = prod_response.json()
        assert prod_data["environment"] == "production"
        assert prod_data["deployments"][0]["status"] == "SUCCESS"
        
        # Fetch staging deployments
        staging_response = client.get(
            "/api/railway/projects/project-1/environments/staging/deployments"
        )
        assert staging_response.status_code == 200
        staging_data = staging_response.json()
        assert staging_data["environment"] == "staging"
        assert staging_data["deployments"][0]["status"] == "BUILDING"

    @patch("railway_router.get_railway_client")
    def test_deployment_trigger_and_monitoring(self, mock_get_client):
        """
        Test triggering a deployment and monitoring its progress.
        
        Simulates:
        1. Triggering a new deployment
        2. Monitoring deployment status changes
        3. Verifying deployment completion
        """
        mock_client = AsyncMock()
        
        # Mock deployment trigger
        mock_client.trigger_deployment.return_value = {
            "id": "new-deploy-1",
            "status": "INITIALIZING",
            "createdAt": "2024-01-15T10:30:00Z"
        }
        
        # Mock deployment status progression
        deployment_statuses = [
            {"id": "new-deploy-1", "status": "INITIALIZING"},
            {"id": "new-deploy-1", "status": "BUILDING"},
            {"id": "new-deploy-1", "status": "DEPLOYING"},
            {"id": "new-deploy-1", "status": "SUCCESS"}
        ]
        
        status_index = [0]  # Use list to allow modification in nested function
        
        def get_deployments(*args, **kwargs):
            current_status = deployment_statuses[min(status_index[0], len(deployment_statuses) - 1)]
            status_index[0] += 1
            return [current_status]
        
        mock_client.get_service_deployments.side_effect = get_deployments
        mock_get_client.return_value = mock_client
        
        # Trigger deployment
        trigger_response = client.post(
            "/api/railway/deployments/trigger",
            json={
                "service_id": "service-api",
                "environment_id": "env-production"
            }
        )
        assert trigger_response.status_code == 200
        trigger_data = trigger_response.json()
        assert trigger_data["success"] is True
        assert trigger_data["deployment"]["status"] == "INITIALIZING"
        
        # Monitor deployment progress
        service_id = "service-api"
        
        # Check 1: INITIALIZING
        status_response = client.get(f"/api/railway/services/{service_id}/deployments?limit=1")
        assert status_response.status_code == 200
        assert status_response.json()["deployments"][0]["status"] == "INITIALIZING"
        
        # Check 2: BUILDING
        status_response = client.get(f"/api/railway/services/{service_id}/deployments?limit=1")
        assert status_response.json()["deployments"][0]["status"] == "BUILDING"
        
        # Check 3: DEPLOYING
        status_response = client.get(f"/api/railway/services/{service_id}/deployments?limit=1")
        assert status_response.json()["deployments"][0]["status"] == "DEPLOYING"
        
        # Check 4: SUCCESS
        status_response = client.get(f"/api/railway/services/{service_id}/deployments?limit=1")
        assert status_response.json()["deployments"][0]["status"] == "SUCCESS"

    @patch("railway_router.get_railway_client")
    def test_deployment_logs_retrieval(self, mock_get_client):
        """
        Test retrieving deployment logs for troubleshooting.
        """
        mock_client = AsyncMock()
        
        # Mock deployment logs
        mock_client.get_deployment_logs.return_value = [
            {
                "id": "log-1",
                "message": "Starting deployment...",
                "timestamp": "2024-01-15T10:00:00Z",
                "severity": "INFO"
            },
            {
                "id": "log-2",
                "message": "Building Docker image...",
                "timestamp": "2024-01-15T10:00:30Z",
                "severity": "INFO"
            },
            {
                "id": "log-3",
                "message": "Deployment successful",
                "timestamp": "2024-01-15T10:05:00Z",
                "severity": "INFO"
            }
        ]
        mock_get_client.return_value = mock_client
        
        # Fetch deployment logs
        logs_response = client.get("/api/railway/deployments/deploy-123/logs?limit=100")
        assert logs_response.status_code == 200
        logs_data = logs_response.json()
        assert len(logs_data["logs"]) == 3
        assert logs_data["logs"][0]["message"] == "Starting deployment..."
        assert logs_data["logs"][-1]["message"] == "Deployment successful"

    @patch("railway_router.get_railway_client")
    def test_error_scenarios(self, mock_get_client):
        """
        Test various error scenarios to ensure graceful handling.
        """
        # Scenario 1: Railway not configured
        mock_get_client.side_effect = ValueError("Railway API token is required")
        
        response = client.get("/api/railway/projects")
        assert response.status_code == 500
        assert "Railway API not configured" in response.json()["detail"]
        
        # Scenario 2: Invalid project ID
        mock_client = AsyncMock()
        mock_client.get_project_services.side_effect = Exception("Project not found")
        mock_get_client.side_effect = None
        mock_get_client.return_value = mock_client
        
        response = client.get("/api/railway/projects/invalid-id/services")
        assert response.status_code == 500
        
        # Scenario 3: Environment not found
        mock_client.get_environment_deployments.return_value = []
        
        response = client.get(
            "/api/railway/projects/project-1/environments/nonexistent/deployments"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["deployments"]) == 0

    @patch("railway_router.get_railway_client")
    def test_auto_refresh_simulation(self, mock_get_client):
        """
        Test simulating auto-refresh behavior (30-second polling).
        
        This verifies that repeated requests work correctly and return updated data.
        """
        mock_client = AsyncMock()
        
        # Simulate deployment status changes over time
        refresh_count = [0]
        
        def get_updated_deployments(*args, **kwargs):
            refresh_count[0] += 1
            
            if refresh_count[0] == 1:
                status = "BUILDING"
            elif refresh_count[0] == 2:
                status = "DEPLOYING"
            else:
                status = "SUCCESS"
            
            return [
                {
                    "id": "deploy-1",
                    "status": status,
                    "createdAt": "2024-01-15T10:00:00Z",
                    "serviceName": "auth-api"
                }
            ]
        
        mock_client.get_environment_deployments.side_effect = get_updated_deployments
        mock_get_client.return_value = mock_client
        
        # Simulate 3 auto-refresh cycles
        for i in range(3):
            response = client.get(
                "/api/railway/projects/project-1/environments/production/deployments"
            )
            assert response.status_code == 200
            deployments = response.json()["deployments"]
            
            if i == 0:
                assert deployments[0]["status"] == "BUILDING"
            elif i == 1:
                assert deployments[0]["status"] == "DEPLOYING"
            else:
                assert deployments[0]["status"] == "SUCCESS"

    @patch("railway_router.get_railway_client")
    def test_filtering_and_pagination(self, mock_get_client):
        """
        Test deployment filtering and pagination features.
        """
        mock_client = AsyncMock()
        
        # Mock multiple deployments
        all_deployments = [
            {
                "id": f"deploy-{i}",
                "status": "SUCCESS" if i < 5 else "BUILDING",
                "environmentId": "env-production" if i < 7 else "env-staging"
            }
            for i in range(10)
        ]
        
        def get_filtered_deployments(service_id, environment_id=None, limit=10):
            filtered = all_deployments
            
            if environment_id:
                filtered = [d for d in filtered if d["environmentId"] == environment_id]
            
            return filtered[:limit]
        
        mock_client.get_service_deployments.side_effect = get_filtered_deployments
        mock_get_client.return_value = mock_client
        
        # Test with limit
        response = client.get("/api/railway/services/service-1/deployments?limit=5")
        assert response.status_code == 200
        assert len(response.json()["deployments"]) == 5
        
        # Test with environment filter
        response = client.get(
            "/api/railway/services/service-1/deployments"
            "?environment_id=env-production&limit=10"
        )
        assert response.status_code == 200
        deployments = response.json()["deployments"]
        assert len(deployments) == 7
        assert all(d["environmentId"] == "env-production" for d in deployments)


class TestRailwayAPIRateLimiting:
    """
    Test rate limiting considerations for Railway API.
    """

    @patch("railway_router.get_railway_client")
    def test_concurrent_requests_handling(self, mock_get_client):
        """
        Test handling multiple concurrent requests (e.g., multiple users).
        """
        mock_client = AsyncMock()
        mock_client.get_projects.return_value = [
            {"id": "project-1", "name": "Test"}
        ]
        mock_get_client.return_value = mock_client
        
        # Simulate 5 concurrent requests
        responses = []
        for _ in range(5):
            response = client.get("/api/railway/projects")
            responses.append(response)
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        
        # Verify Railway client was called 5 times
        assert mock_client.get_projects.call_count == 5
