"""
backend/tests/test_railway_client.py
════════════════════════════════════
Unit tests for Railway GraphQL API client.
Tests SDT1-58: UAT Deploy tab - wire to Railway GraphQL API
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from railway_client import RailwayClient, RailwayAPIError


@pytest.fixture
def railway_client():
    """Create a Railway client with mock token."""
    return RailwayClient(api_token="test-token-123")


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client."""
    with patch('railway_client.httpx.AsyncClient') as mock:
        yield mock


class TestRailwayClientInit:
    """Tests for RailwayClient initialization."""
    
    def test_init_with_token(self):
        """Test initialization with explicit token."""
        client = RailwayClient(api_token="my-token")
        assert client.api_token == "my-token"
        assert "Bearer my-token" in client.headers["Authorization"]
    
    def test_init_from_env(self, monkeypatch):
        """Test initialization from environment variable."""
        monkeypatch.setenv("RAILWAY_API_TOKEN", "env-token")
        client = RailwayClient()
        assert client.api_token == "env-token"
    
    def test_init_no_token_raises_error(self, monkeypatch):
        """Test that initialization without token raises error."""
        monkeypatch.delenv("RAILWAY_API_TOKEN", raising=False)
        with pytest.raises(ValueError, match="Railway API token is required"):
            RailwayClient()


class TestRailwayClientExecuteQuery:
    """Tests for GraphQL query execution."""
    
    @pytest.mark.asyncio
    async def test_execute_query_success(self, railway_client, mock_httpx_client):
        """Test successful query execution."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"project": {"id": "123", "name": "Test Project"}}
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        
        result = await railway_client._execute_query("query { project { id name } }")
        
        assert result == {"project": {"id": "123", "name": "Test Project"}}
        mock_client_instance.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_query_with_variables(self, railway_client, mock_httpx_client):
        """Test query execution with variables."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"result": "ok"}}
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        
        variables = {"projectId": "abc123"}
        await railway_client._execute_query("query($projectId: String!) {}", variables)
        
        call_args = mock_client_instance.post.call_args
        assert call_args.kwargs["json"]["variables"] == variables
    
    @pytest.mark.asyncio
    async def test_execute_query_graphql_error(self, railway_client, mock_httpx_client):
        """Test handling of GraphQL errors."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "errors": [
                {"message": "Field not found"},
                {"message": "Invalid query"}
            ]
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        
        with pytest.raises(RailwayAPIError, match="GraphQL errors"):
            await railway_client._execute_query("query { invalid }")
    
    @pytest.mark.asyncio
    async def test_execute_query_http_error(self, railway_client, mock_httpx_client):
        """Test handling of HTTP errors."""
        import httpx
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        
        with pytest.raises(RailwayAPIError, match="Railway API request failed"):
            await railway_client._execute_query("query { test }")


class TestRailwayClientGetProject:
    """Tests for get_project method."""
    
    @pytest.mark.asyncio
    async def test_get_project_success(self, railway_client):
        """Test successful project retrieval."""
        mock_data = {
            "project": {
                "id": "proj123",
                "name": "My Project",
                "description": "Test project",
                "services": {"edges": []},
                "environments": {"edges": []}
            }
        }
        
        with patch.object(railway_client, '_execute_query', return_value=mock_data):
            result = await railway_client.get_project("proj123")
            
            assert result["id"] == "proj123"
            assert result["name"] == "My Project"


class TestRailwayClientListServices:
    """Tests for list_services method."""
    
    @pytest.mark.asyncio
    async def test_list_services_success(self, railway_client):
        """Test successful service listing."""
        mock_data = {
            "project": {
                "services": {
                    "edges": [
                        {"node": {"id": "svc1", "name": "API Service"}},
                        {"node": {"id": "svc2", "name": "Frontend"}},
                    ]
                }
            }
        }
        
        with patch.object(railway_client, '_execute_query', return_value=mock_data):
            result = await railway_client.list_services("proj123")
            
            assert len(result) == 2
            assert result[0]["id"] == "svc1"
            assert result[1]["name"] == "Frontend"


class TestRailwayClientTriggerDeployment:
    """Tests for trigger_deployment method."""
    
    @pytest.mark.asyncio
    async def test_trigger_deployment_success(self, railway_client):
        """Test successful deployment triggering."""
        mock_data = {
            "serviceDeploy": {
                "id": "deploy123",
                "status": "BUILDING",
                "createdAt": "2024-01-15T10:00:00Z",
                "staticUrl": "https://my-app.railway.app"
            }
        }
        
        with patch.object(railway_client, '_execute_query', return_value=mock_data):
            result = await railway_client.trigger_deployment(
                service_id="svc123",
                environment_id="env123"
            )
            
            assert result["id"] == "deploy123"
            assert result["status"] == "BUILDING"
    
    @pytest.mark.asyncio
    async def test_trigger_deployment_no_data(self, railway_client):
        """Test deployment triggering with no data returned."""
        mock_data = {}
        
        with patch.object(railway_client, '_execute_query', return_value=mock_data):
            with pytest.raises(RailwayAPIError, match="Failed to trigger deployment"):
                await railway_client.trigger_deployment(
                    service_id="svc123",
                    environment_id="env123"
                )


class TestRailwayClientGetDeploymentStatus:
    """Tests for get_deployment_status method."""
    
    @pytest.mark.asyncio
    async def test_get_deployment_status_success(self, railway_client):
        """Test successful deployment status retrieval."""
        mock_data = {
            "deployment": {
                "id": "deploy123",
                "status": "SUCCESS",
                "createdAt": "2024-01-15T10:00:00Z",
                "updatedAt": "2024-01-15T10:05:00Z",
                "environment": {"id": "env123", "name": "UAT"},
                "service": {"id": "svc123", "name": "API"}
            }
        }
        
        with patch.object(railway_client, '_execute_query', return_value=mock_data):
            result = await railway_client.get_deployment_status("deploy123")
            
            assert result["id"] == "deploy123"
            assert result["status"] == "SUCCESS"
            assert result["environment"]["name"] == "UAT"


class TestRailwayClientGetServiceDeployments:
    """Tests for get_service_deployments method."""
    
    @pytest.mark.asyncio
    async def test_get_service_deployments_success(self, railway_client):
        """Test successful service deployments retrieval."""
        mock_data = {
            "deployments": {
                "edges": [
                    {"node": {"id": "d1", "status": "SUCCESS"}},
                    {"node": {"id": "d2", "status": "BUILDING"}},
                ]
            }
        }
        
        with patch.object(railway_client, '_execute_query', return_value=mock_data):
            result = await railway_client.get_service_deployments("svc123", limit=5)
            
            assert len(result) == 2
            assert result[0]["id"] == "d1"
            assert result[1]["status"] == "BUILDING"


class TestRailwayClientGetEnvironments:
    """Tests for get_environments method."""
    
    @pytest.mark.asyncio
    async def test_get_environments_success(self, railway_client):
        """Test successful environments retrieval."""
        mock_data = {
            "project": {
                "environments": {
                    "edges": [
                        {"node": {"id": "env1", "name": "Production"}},
                        {"node": {"id": "env2", "name": "UAT"}},
                    ]
                }
            }
        }
        
        with patch.object(railway_client, '_execute_query', return_value=mock_data):
            result = await railway_client.get_environments("proj123")
            
            assert len(result) == 2
            assert result[0]["name"] == "Production"
            assert result[1]["name"] == "UAT"


def test_get_railway_client():
    """Test get_railway_client factory function."""
    from railway_client import get_railway_client
    
    with patch.dict('os.environ', {'RAILWAY_API_TOKEN': 'test-token'}):
        client = get_railway_client()
        assert isinstance(client, RailwayClient)
        assert client.api_token == "test-token"
