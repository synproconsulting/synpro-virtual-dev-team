"""
Tests for Railway GraphQL API client.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from railway_client import RailwayClient, get_railway_client


class TestRailwayClient:
    """Test suite for RailwayClient class."""

    def test_init_with_token(self):
        """Test initialization with explicit token."""
        client = RailwayClient(api_token="test_token")
        assert client.api_token == "test_token"
        assert client.headers["Authorization"] == "Bearer test_token"

    def test_init_with_env_token(self, monkeypatch):
        """Test initialization with environment variable token."""
        monkeypatch.setenv("RAILWAY_API_TOKEN", "env_token")
        client = RailwayClient()
        assert client.api_token == "env_token"

    def test_init_without_token(self, monkeypatch):
        """Test initialization fails without token."""
        monkeypatch.delenv("RAILWAY_API_TOKEN", raising=False)
        with pytest.raises(ValueError, match="Railway API token is required"):
            RailwayClient()

    @pytest.mark.asyncio
    async def test_execute_query_success(self):
        """Test successful GraphQL query execution."""
        client = RailwayClient(api_token="test_token")
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"projects": {"edges": []}}
        }
        mock_response.raise_for_status = Mock()
        
        with patch("httpx.AsyncClient") as mock_async_client:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.post.return_value = mock_response
            mock_async_client.return_value = mock_client
            
            result = await client._execute_query("query { projects { edges { node { id } } } }")
            
            assert result == {"projects": {"edges": []}}

    @pytest.mark.asyncio
    async def test_execute_query_with_graphql_errors(self):
        """Test query execution with GraphQL errors."""
        client = RailwayClient(api_token="test_token")
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "errors": [{"message": "Invalid query"}]
        }
        mock_response.raise_for_status = Mock()
        
        with patch("httpx.AsyncClient") as mock_async_client:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.post.return_value = mock_response
            mock_async_client.return_value = mock_client
            
            with pytest.raises(Exception, match="GraphQL errors: Invalid query"):
                await client._execute_query("invalid query")

    @pytest.mark.asyncio
    async def test_get_projects(self):
        """Test fetching projects."""
        client = RailwayClient(api_token="test_token")
        
        mock_data = {
            "projects": {
                "edges": [
                    {
                        "node": {
                            "id": "project1",
                            "name": "Test Project",
                            "description": "A test project",
                            "createdAt": "2024-01-01T00:00:00Z",
                            "updatedAt": "2024-01-01T00:00:00Z"
                        }
                    }
                ]
            }
        }
        
        with patch.object(client, "_execute_query", return_value=mock_data):
            projects = await client.get_projects()
            
            assert len(projects) == 1
            assert projects[0]["id"] == "project1"
            assert projects[0]["name"] == "Test Project"

    @pytest.mark.asyncio
    async def test_get_project_services(self):
        """Test fetching services for a project."""
        client = RailwayClient(api_token="test_token")
        
        mock_data = {
            "project": {
                "services": {
                    "edges": [
                        {
                            "node": {
                                "id": "service1",
                                "name": "API Service",
                                "createdAt": "2024-01-01T00:00:00Z",
                                "updatedAt": "2024-01-01T00:00:00Z"
                            }
                        }
                    ]
                }
            }
        }
        
        with patch.object(client, "_execute_query", return_value=mock_data):
            services = await client.get_project_services("project1")
            
            assert len(services) == 1
            assert services[0]["id"] == "service1"
            assert services[0]["name"] == "API Service"

    @pytest.mark.asyncio
    async def test_get_service_deployments(self):
        """Test fetching deployments for a service."""
        client = RailwayClient(api_token="test_token")
        
        mock_data = {
            "service": {
                "id": "service1",
                "name": "API Service",
                "deployments": {
                    "edges": [
                        {
                            "node": {
                                "id": "deployment1",
                                "status": "SUCCESS",
                                "createdAt": "2024-01-01T00:00:00Z",
                                "updatedAt": "2024-01-01T00:01:00Z",
                                "staticUrl": "https://api.railway.app",
                                "meta": {},
                                "environmentId": "env1"
                            }
                        }
                    ]
                }
            }
        }
        
        with patch.object(client, "_execute_query", return_value=mock_data):
            deployments = await client.get_service_deployments("service1", limit=10)
            
            assert len(deployments) == 1
            assert deployments[0]["id"] == "deployment1"
            assert deployments[0]["status"] == "SUCCESS"

    @pytest.mark.asyncio
    async def test_get_service_deployments_with_environment_filter(self):
        """Test fetching deployments filtered by environment."""
        client = RailwayClient(api_token="test_token")
        
        mock_data = {
            "service": {
                "id": "service1",
                "name": "API Service",
                "deployments": {
                    "edges": [
                        {
                            "node": {
                                "id": "deployment1",
                                "status": "SUCCESS",
                                "createdAt": "2024-01-01T00:00:00Z",
                                "environmentId": "env1"
                            }
                        },
                        {
                            "node": {
                                "id": "deployment2",
                                "status": "SUCCESS",
                                "createdAt": "2024-01-01T01:00:00Z",
                                "environmentId": "env2"
                            }
                        }
                    ]
                }
            }
        }
        
        with patch.object(client, "_execute_query", return_value=mock_data):
            deployments = await client.get_service_deployments(
                "service1", 
                environment_id="env1",
                limit=10
            )
            
            assert len(deployments) == 1
            assert deployments[0]["id"] == "deployment1"
            assert deployments[0]["environmentId"] == "env1"

    @pytest.mark.asyncio
    async def test_get_environment_deployments(self):
        """Test fetching deployments for an environment."""
        client = RailwayClient(api_token="test_token")
        
        mock_data = {
            "project": {
                "id": "project1",
                "name": "Test Project",
                "environments": {
                    "edges": [
                        {
                            "node": {
                                "id": "env1",
                                "name": "production",
                                "deployments": {
                                    "edges": [
                                        {
                                            "node": {
                                                "id": "deployment1",
                                                "status": "SUCCESS",
                                                "createdAt": "2024-01-01T00:00:00Z",
                                                "updatedAt": "2024-01-01T00:01:00Z",
                                                "staticUrl": "https://api.railway.app",
                                                "serviceId": "service1"
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                },
                "services": {
                    "edges": [
                        {
                            "node": {
                                "id": "service1",
                                "name": "API Service"
                            }
                        }
                    ]
                }
            }
        }
        
        with patch.object(client, "_execute_query", return_value=mock_data):
            deployments = await client.get_environment_deployments(
                "project1", 
                "production"
            )
            
            assert len(deployments) == 1
            assert deployments[0]["id"] == "deployment1"
            assert deployments[0]["serviceName"] == "API Service"

    @pytest.mark.asyncio
    async def test_get_environment_deployments_not_found(self):
        """Test fetching deployments for non-existent environment."""
        client = RailwayClient(api_token="test_token")
        
        mock_data = {
            "project": {
                "id": "project1",
                "name": "Test Project",
                "environments": {
                    "edges": [
                        {
                            "node": {
                                "id": "env1",
                                "name": "production",
                                "deployments": {"edges": []}
                            }
                        }
                    ]
                },
                "services": {"edges": []}
            }
        }
        
        with patch.object(client, "_execute_query", return_value=mock_data):
            deployments = await client.get_environment_deployments(
                "project1", 
                "staging"
            )
            
            assert deployments == []

    @pytest.mark.asyncio
    async def test_trigger_deployment(self):
        """Test triggering a deployment."""
        client = RailwayClient(api_token="test_token")
        
        mock_data = {
            "serviceDeploy": {
                "id": "deployment1",
                "status": "INITIALIZING",
                "createdAt": "2024-01-01T00:00:00Z"
            }
        }
        
        with patch.object(client, "_execute_query", return_value=mock_data):
            result = await client.trigger_deployment("service1", "env1")
            
            assert result["id"] == "deployment1"
            assert result["status"] == "INITIALIZING"

    def test_get_railway_client_success(self, monkeypatch):
        """Test factory function with configured token."""
        monkeypatch.setenv("RAILWAY_API_TOKEN", "test_token")
        client = get_railway_client()
        assert isinstance(client, RailwayClient)
        assert client.api_token == "test_token"

    def test_get_railway_client_no_token(self, monkeypatch):
        """Test factory function without token."""
        monkeypatch.delenv("RAILWAY_API_TOKEN", raising=False)
        with pytest.raises(ValueError, match="Railway API token is required"):
            get_railway_client()
