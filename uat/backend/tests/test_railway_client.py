"""
Tests for Railway GraphQL API client.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from railway_client import (
    RailwayClient,
    RailwayClientError,
    RailwayService,
    RailwayEnvironment,
    RailwayDeployment,
)


@pytest.fixture
def railway_client():
    """Create Railway client with mock credentials."""
    with patch.dict('os.environ', {
        'RAILWAY_API_TOKEN': 'test-token',
        'RAILWAY_PROJECT_ID': 'test-project-id',
        'RAILWAY_ENVIRONMENT_ID': 'test-env-id',
    }):
        return RailwayClient()


@pytest.fixture
def mock_project_data():
    """Mock project data from Railway API."""
    return {
        "project": {
            "id": "test-project-id",
            "name": "Test Project",
            "description": "Test Description",
            "createdAt": "2024-01-01T00:00:00Z",
            "environments": {
                "edges": [
                    {
                        "node": {
                            "id": "env-1",
                            "name": "UAT",
                            "serviceInstances": {
                                "edges": [
                                    {
                                        "node": {
                                            "id": "si-1",
                                            "serviceId": "service-1",
                                            "latestDeployment": {
                                                "id": "deployment-1",
                                                "status": "SUCCESS",
                                                "createdAt": "2024-01-01T12:00:00Z",
                                            },
                                        },
                                    },
                                ],
                            },
                        },
                    },
                ],
            },
            "services": {
                "edges": [
                    {
                        "node": {
                            "id": "service-1",
                            "name": "API Service",
                            "icon": "🚀",
                            "createdAt": "2024-01-01T00:00:00Z",
                        },
                    },
                    {
                        "node": {
                            "id": "service-2",
                            "name": "Frontend App",
                            "icon": "⚛️",
                            "createdAt": "2024-01-01T00:00:00Z",
                        },
                    },
                ],
            },
        },
    }


@pytest.fixture
def mock_deployment_data():
    """Mock deployment data from Railway API."""
    return {
        "deployment": {
            "id": "deployment-1",
            "status": "SUCCESS",
            "createdAt": "2024-01-01T12:00:00Z",
            "environment": {
                "name": "UAT",
            },
            "service": {
                "name": "API Service",
            },
            "url": "https://api.example.com",
        },
    }


class TestRailwayClientInit:
    """Tests for RailwayClient initialization."""

    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        with patch.dict('os.environ', {
            'RAILWAY_API_TOKEN': 'test-token',
            'RAILWAY_PROJECT_ID': 'test-project',
        }):
            client = RailwayClient()
            assert client.api_token == 'test-token'
            assert client.project_id == 'test-project'

    def test_init_with_params(self):
        """Test initialization with explicit parameters."""
        client = RailwayClient(
            api_token='param-token',
            project_id='param-project',
            environment_id='param-env',
        )
        assert client.api_token == 'param-token'
        assert client.project_id == 'param-project'
        assert client.environment_id == 'param-env'

    def test_init_missing_token(self):
        """Test initialization fails without API token."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(RailwayClientError, match="RAILWAY_API_TOKEN"):
                RailwayClient()

    def test_init_missing_project_id(self):
        """Test initialization fails without project ID."""
        with patch.dict('os.environ', {'RAILWAY_API_TOKEN': 'test'}, clear=True):
            with pytest.raises(RailwayClientError, match="RAILWAY_PROJECT_ID"):
                RailwayClient()


class TestRailwayClientQueries:
    """Tests for Railway client query methods."""

    @pytest.mark.asyncio
    async def test_execute_query_success(self, railway_client):
        """Test successful GraphQL query execution."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"test": "result"}}
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await railway_client._execute_query("query { test }")
            assert result == {"test": "result"}

    @pytest.mark.asyncio
    async def test_execute_query_with_errors(self, railway_client):
        """Test query execution with GraphQL errors."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "errors": [{"message": "Test error"}],
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises(RailwayClientError, match="Test error"):
                await railway_client._execute_query("query { test }")

    @pytest.mark.asyncio
    async def test_execute_query_http_error(self, railway_client):
        """Test query execution with HTTP error."""
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.HTTPError("Connection failed")
            
            with pytest.raises(RailwayClientError, match="HTTP error"):
                await railway_client._execute_query("query { test }")

    @pytest.mark.asyncio
    async def test_get_project_info(self, railway_client, mock_project_data):
        """Test getting project information."""
        with patch.object(
            railway_client,
            '_execute_query',
            new_callable=AsyncMock,
        ) as mock_query:
            mock_query.return_value = mock_project_data
            
            result = await railway_client.get_project_info()
            assert result["id"] == "test-project-id"
            assert result["name"] == "Test Project"

    @pytest.mark.asyncio
    async def test_list_services(self, railway_client, mock_project_data):
        """Test listing services."""
        with patch.object(
            railway_client,
            'get_project_info',
            new_callable=AsyncMock,
        ) as mock_info:
            mock_info.return_value = mock_project_data["project"]
            
            services = await railway_client.list_services()
            assert len(services) == 2
            assert isinstance(services[0], RailwayService)
            assert services[0].name == "API Service"
            assert services[1].name == "Frontend App"

    @pytest.mark.asyncio
    async def test_list_environments(self, railway_client, mock_project_data):
        """Test listing environments."""
        with patch.object(
            railway_client,
            'get_project_info',
            new_callable=AsyncMock,
        ) as mock_info:
            mock_info.return_value = mock_project_data["project"]
            
            environments = await railway_client.list_environments()
            assert len(environments) == 1
            assert isinstance(environments[0], RailwayEnvironment)
            assert environments[0].name == "UAT"


class TestRailwayClientDeployments:
    """Tests for Railway client deployment methods."""

    @pytest.mark.asyncio
    async def test_trigger_deployment_success(self, railway_client):
        """Test successful deployment trigger."""
        mock_result = {
            "deploymentTrigger": {
                "id": "deployment-123",
                "status": "BUILDING",
                "createdAt": "2024-01-01T12:00:00Z",
            },
        }
        
        with patch.object(
            railway_client,
            '_execute_query',
            new_callable=AsyncMock,
        ) as mock_query:
            mock_query.return_value = mock_result
            
            deployment_id = await railway_client.trigger_deployment("service-1")
            assert deployment_id == "deployment-123"

    @pytest.mark.asyncio
    async def test_trigger_deployment_missing_env(self):
        """Test deployment trigger without environment ID."""
        with patch.dict('os.environ', {
            'RAILWAY_API_TOKEN': 'test-token',
            'RAILWAY_PROJECT_ID': 'test-project-id',
        }, clear=True):
            client = RailwayClient()
            
            with pytest.raises(RailwayClientError, match="Environment ID is required"):
                await client.trigger_deployment("service-1")

    @pytest.mark.asyncio
    async def test_get_deployment_status(self, railway_client, mock_deployment_data):
        """Test getting deployment status."""
        with patch.object(
            railway_client,
            '_execute_query',
            new_callable=AsyncMock,
        ) as mock_query:
            mock_query.return_value = mock_deployment_data
            
            deployment = await railway_client.get_deployment_status("deployment-1")
            assert isinstance(deployment, RailwayDeployment)
            assert deployment.id == "deployment-1"
            assert deployment.status == "SUCCESS"
            assert deployment.service_name == "API Service"
            assert deployment.environment_name == "UAT"

    @pytest.mark.asyncio
    async def test_get_deployment_status_not_found(self, railway_client):
        """Test getting status for non-existent deployment."""
        with patch.object(
            railway_client,
            '_execute_query',
            new_callable=AsyncMock,
        ) as mock_query:
            mock_query.return_value = {}
            
            with pytest.raises(RailwayClientError, match="not found"):
                await railway_client.get_deployment_status("nonexistent")

    @pytest.mark.asyncio
    async def test_list_deployments(self, railway_client, mock_project_data, mock_deployment_data):
        """Test listing deployments."""
        with patch.object(
            railway_client,
            'get_project_info',
            new_callable=AsyncMock,
        ) as mock_info:
            mock_info.return_value = mock_project_data["project"]
            
            with patch.object(
                railway_client,
                'get_deployment_status',
                new_callable=AsyncMock,
            ) as mock_status:
                mock_status.return_value = RailwayDeployment(
                    id="deployment-1",
                    status="SUCCESS",
                    environment_name="UAT",
                    service_name="API Service",
                    created_at="2024-01-01T12:00:00Z",
                )
                
                deployments = await railway_client.list_deployments()
                assert len(deployments) == 1
                assert deployments[0].id == "deployment-1"

    @pytest.mark.asyncio
    async def test_get_service_logs(self, railway_client):
        """Test getting service logs."""
        mock_result = {
            "deploymentLogs": [
                {"message": "Log line 1", "timestamp": "2024-01-01T12:00:00Z"},
                {"message": "Log line 2", "timestamp": "2024-01-01T12:00:01Z"},
            ],
        }
        
        with patch.object(
            railway_client,
            '_execute_query',
            new_callable=AsyncMock,
        ) as mock_query:
            mock_query.return_value = mock_result
            
            logs = await railway_client.get_service_logs("deployment-1")
            assert len(logs) == 2
            assert logs[0] == "Log line 1"
            assert logs[1] == "Log line 2"
