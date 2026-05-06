"""
test_railway_api.py
===================
Unit tests for Railway GraphQL API client.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from railway_api import RailwayClient, RailwayAPIError, get_railway_client


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables."""
    monkeypatch.setenv("RAILWAY_API_TOKEN", "test-token-123")


@pytest.fixture
def railway_client(mock_env):
    """Create a Railway client instance for testing."""
    return RailwayClient(api_token="test-token-123")


class TestRailwayClientInit:
    """Test Railway client initialization."""
    
    def test_init_with_token(self):
        """Test initialization with explicit token."""
        client = RailwayClient(api_token="test-token")
        assert client.api_token == "test-token"
        assert client.base_url == "https://backboard.railway.app/graphql/v2"
    
    def test_init_from_env(self, mock_env):
        """Test initialization from environment variable."""
        client = RailwayClient()
        assert client.api_token == "test-token-123"
    
    def test_init_without_token(self, monkeypatch):
        """Test initialization fails without token."""
        monkeypatch.delenv("RAILWAY_API_TOKEN", raising=False)
        with pytest.raises(RailwayAPIError, match="Railway API token not provided"):
            RailwayClient()


class TestRailwayClientExecuteQuery:
    """Test GraphQL query execution."""
    
    @pytest.mark.asyncio
    async def test_execute_query_success(self, railway_client):
        """Test successful query execution."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "projects": {"edges": []}
            }
        }
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await railway_client._execute_query("query { projects }")
            
            assert result == {"projects": {"edges": []}}
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_query_with_variables(self, railway_client):
        """Test query execution with variables."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"project": {"id": "123"}}}
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            variables = {"projectId": "123"}
            result = await railway_client._execute_query(
                "query($projectId: String!) { project(id: $projectId) }",
                variables
            )
            
            assert result == {"project": {"id": "123"}}
            
            # Verify variables were passed
            call_args = mock_post.call_args
            assert call_args[1]["json"]["variables"] == variables
    
    @pytest.mark.asyncio
    async def test_execute_query_graphql_errors(self, railway_client):
        """Test handling of GraphQL errors."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "errors": [
                {"message": "Invalid project ID"},
                {"message": "Unauthorized"}
            ]
        }
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises(RailwayAPIError, match="Invalid project ID; Unauthorized"):
                await railway_client._execute_query("query { projects }")
    
    @pytest.mark.asyncio
    async def test_execute_query_http_error(self, railway_client):
        """Test handling of HTTP errors."""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = Exception("Connection error")
            
            with pytest.raises(RailwayAPIError, match="Error communicating with Railway API"):
                await railway_client._execute_query("query { projects }")


class TestRailwayClientProjects:
    """Test project-related methods."""
    
    @pytest.mark.asyncio
    async def test_get_projects(self, railway_client):
        """Test fetching projects."""
        mock_data = {
            "projects": {
                "edges": [
                    {
                        "node": {
                            "id": "proj-1",
                            "name": "Test Project",
                            "description": "A test project",
                            "createdAt": "2024-01-01T00:00:00Z"
                        }
                    }
                ]
            }
        }
        
        with patch.object(
            railway_client,
            "_execute_query",
            new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = mock_data
            
            projects = await railway_client.get_projects()
            
            assert len(projects) == 1
            assert projects[0]["id"] == "proj-1"
            assert projects[0]["name"] == "Test Project"
    
    @pytest.mark.asyncio
    async def test_get_project_services(self, railway_client):
        """Test fetching project services."""
        mock_data = {
            "project": {
                "services": {
                    "edges": [
                        {
                            "node": {
                                "id": "svc-1",
                                "name": "API Service",
                                "icon": "🚀",
                                "createdAt": "2024-01-01T00:00:00Z"
                            }
                        }
                    ]
                }
            }
        }
        
        with patch.object(
            railway_client,
            "_execute_query",
            new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = mock_data
            
            services = await railway_client.get_project_services("proj-1")
            
            assert len(services) == 1
            assert services[0]["id"] == "svc-1"
            assert services[0]["name"] == "API Service"
    
    @pytest.mark.asyncio
    async def test_get_project_environments(self, railway_client):
        """Test fetching project environments."""
        mock_data = {
            "project": {
                "environments": {
                    "edges": [
                        {
                            "node": {
                                "id": "env-1",
                                "name": "production",
                                "createdAt": "2024-01-01T00:00:00Z"
                            }
                        },
                        {
                            "node": {
                                "id": "env-2",
                                "name": "uat",
                                "createdAt": "2024-01-02T00:00:00Z"
                            }
                        }
                    ]
                }
            }
        }
        
        with patch.object(
            railway_client,
            "_execute_query",
            new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = mock_data
            
            environments = await railway_client.get_project_environments("proj-1")
            
            assert len(environments) == 2
            assert environments[0]["name"] == "production"
            assert environments[1]["name"] == "uat"


class TestRailwayClientDeployments:
    """Test deployment-related methods."""
    
    @pytest.mark.asyncio
    async def test_get_service_deployments(self, railway_client):
        """Test fetching service deployments."""
        mock_data = {
            "service": {
                "deployments": {
                    "edges": [
                        {
                            "node": {
                                "id": "dep-1",
                                "status": "SUCCESS",
                                "createdAt": "2024-01-01T00:00:00Z",
                                "updatedAt": "2024-01-01T00:05:00Z",
                                "staticUrl": "https://example.railway.app",
                                "meta": {}
                            }
                        }
                    ]
                }
            }
        }
        
        with patch.object(
            railway_client,
            "_execute_query",
            new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = mock_data
            
            deployments = await railway_client.get_service_deployments("svc-1")
            
            assert len(deployments) == 1
            assert deployments[0]["id"] == "dep-1"
            assert deployments[0]["status"] == "SUCCESS"
    
    @pytest.mark.asyncio
    async def test_trigger_deployment(self, railway_client):
        """Test triggering a deployment."""
        mock_data = {
            "deploymentTrigger": {
                "id": "new-dep-1",
                "status": "QUEUED",
                "createdAt": "2024-01-01T00:00:00Z"
            }
        }
        
        with patch.object(
            railway_client,
            "_execute_query",
            new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = mock_data
            
            deployment = await railway_client.trigger_deployment("svc-1", "env-1")
            
            assert deployment["id"] == "new-dep-1"
            assert deployment["status"] == "QUEUED"
            
            # Verify correct variables were passed
            call_args = mock_query.call_args
            variables = call_args[0][1]
            assert variables["serviceId"] == "svc-1"
            assert variables["environmentId"] == "env-1"
    
    @pytest.mark.asyncio
    async def test_trigger_deployment_no_data(self, railway_client):
        """Test triggering deployment with no response data."""
        with patch.object(
            railway_client,
            "_execute_query",
            new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = {}
            
            with pytest.raises(RailwayAPIError, match="Deployment trigger returned no data"):
                await railway_client.trigger_deployment("svc-1", "env-1")
    
    @pytest.mark.asyncio
    async def test_get_deployment_status(self, railway_client):
        """Test fetching deployment status."""
        mock_data = {
            "deployment": {
                "id": "dep-1",
                "status": "BUILDING",
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-01T00:02:00Z",
                "staticUrl": None,
                "meta": {"buildLog": "..."}
            }
        }
        
        with patch.object(
            railway_client,
            "_execute_query",
            new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = mock_data
            
            deployment = await railway_client.get_deployment_status("dep-1")
            
            assert deployment["id"] == "dep-1"
            assert deployment["status"] == "BUILDING"
    
    @pytest.mark.asyncio
    async def test_get_deployment_status_not_found(self, railway_client):
        """Test fetching non-existent deployment."""
        with patch.object(
            railway_client,
            "_execute_query",
            new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = {}
            
            with pytest.raises(RailwayAPIError, match="Deployment dep-1 not found"):
                await railway_client.get_deployment_status("dep-1")


class TestRailwayClientVariables:
    """Test environment variable methods."""
    
    @pytest.mark.asyncio
    async def test_get_service_variables(self, railway_client):
        """Test fetching service environment variables."""
        mock_data = {
            "variables": {
                "edges": [
                    {"node": {"name": "DATABASE_URL", "value": "postgres://..."}},
                    {"node": {"name": "API_KEY", "value": "***"}},
                    {"node": {"name": "PORT", "value": "8000"}}
                ]
            }
        }
        
        with patch.object(
            railway_client,
            "_execute_query",
            new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = mock_data
            
            variables = await railway_client.get_service_variables("svc-1", "env-1")
            
            assert len(variables) == 3
            assert variables["DATABASE_URL"] == "postgres://..."
            assert variables["API_KEY"] == "***"
            assert variables["PORT"] == "8000"


class TestGetRailwayClient:
    """Test factory function."""
    
    @pytest.mark.asyncio
    async def test_get_railway_client(self, mock_env):
        """Test factory function creates client."""
        client = await get_railway_client()
        assert isinstance(client, RailwayClient)
        assert client.api_token == "test-token-123"
    
    @pytest.mark.asyncio
    async def test_get_railway_client_no_token(self, monkeypatch):
        """Test factory function fails without token."""
        monkeypatch.delenv("RAILWAY_API_TOKEN", raising=False)
        with pytest.raises(RailwayAPIError):
            await get_railway_client()