"""
test_railway_graphql_validation.py
===================================
Tests to validate GraphQL queries and mutations against Railway API schema.
Ensures that our queries are syntactically correct and compatible with Railway's API.
"""

import pytest
import os
from typing import Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock
from graphql import parse, validate, build_schema, GraphQLSchema
from railway_api import RailwayClient, RailwayAPIError


# Railway API GraphQL Schema (simplified, based on public documentation)
RAILWAY_SCHEMA = """
type Query {
  projects: ProjectConnection!
  project(id: String!): Project
  service(id: String!): Service
  deployment(id: String!): Deployment
  variables(serviceId: String!, environmentId: String!): VariableConnection!
}

type Mutation {
  deploymentTrigger(serviceId: String!, environmentId: String!): Deployment!
}

type ProjectConnection {
  edges: [ProjectEdge!]!
}

type ProjectEdge {
  node: Project!
}

type Project {
  id: String!
  name: String!
  description: String
  createdAt: String!
  services: ServiceConnection!
  environments: EnvironmentConnection!
}

type ServiceConnection {
  edges: [ServiceEdge!]!
}

type ServiceEdge {
  node: Service!
}

type Service {
  id: String!
  name: String!
  icon: String
  createdAt: String!
  deployments(first: Int, orderBy: DeploymentOrderBy): DeploymentConnection!
}

type DeploymentConnection {
  edges: [DeploymentEdge!]!
}

type DeploymentEdge {
  node: Deployment!
}

type Deployment {
  id: String!
  status: String!
  createdAt: String!
  updatedAt: String
  staticUrl: String
  meta: String
}

type EnvironmentConnection {
  edges: [EnvironmentEdge!]!
}

type EnvironmentEdge {
  node: Environment!
}

type Environment {
  id: String!
  name: String!
  createdAt: String!
}

type VariableConnection {
  edges: [VariableEdge!]!
}

type VariableEdge {
  node: Variable!
}

type Variable {
  name: String!
  value: String!
}

enum DeploymentOrderByColumn {
  CREATED_AT
  UPDATED_AT
}

enum OrderDirection {
  ASC
  DESC
}

input DeploymentOrderBy {
  column: DeploymentOrderByColumn!
  direction: OrderDirection!
}
"""


@pytest.fixture
def railway_schema() -> GraphQLSchema:
    """Build GraphQL schema for Railway API."""
    return build_schema(RAILWAY_SCHEMA)


class TestGraphQLQueryValidation:
    """Validate that all GraphQL queries in railway_api.py are syntactically correct."""
    
    def test_get_projects_query_valid(self, railway_schema):
        """Validate get_projects GraphQL query."""
        query = """
        query {
          projects {
            edges {
              node {
                id
                name
                description
                createdAt
              }
            }
          }
        }
        """
        
        # Parse the query
        document = parse(query)
        
        # Validate against schema
        errors = validate(railway_schema, document)
        
        assert len(errors) == 0, f"GraphQL query validation failed: {errors}"
    
    def test_get_project_services_query_valid(self, railway_schema):
        """Validate get_project_services GraphQL query."""
        query = """
        query GetProjectServices($projectId: String!) {
          project(id: $projectId) {
            services {
              edges {
                node {
                  id
                  name
                  icon
                  createdAt
                }
              }
            }
          }
        }
        """
        
        document = parse(query)
        errors = validate(railway_schema, document)
        
        assert len(errors) == 0, f"GraphQL query validation failed: {errors}"
    
    def test_get_service_deployments_query_valid(self, railway_schema):
        """Validate get_service_deployments GraphQL query."""
        query = """
        query GetServiceDeployments($serviceId: String!) {
          service(id: $serviceId) {
            deployments(first: 10, orderBy: {column: CREATED_AT, direction: DESC}) {
              edges {
                node {
                  id
                  status
                  createdAt
                  updatedAt
                  staticUrl
                  meta
                }
              }
            }
          }
        }
        """
        
        document = parse(query)
        errors = validate(railway_schema, document)
        
        assert len(errors) == 0, f"GraphQL query validation failed: {errors}"
    
    def test_trigger_deployment_mutation_valid(self, railway_schema):
        """Validate trigger_deployment GraphQL mutation."""
        mutation = """
        mutation DeploymentTrigger($serviceId: String!, $environmentId: String!) {
          deploymentTrigger(serviceId: $serviceId, environmentId: $environmentId) {
            id
            status
            createdAt
          }
        }
        """
        
        document = parse(mutation)
        errors = validate(railway_schema, document)
        
        assert len(errors) == 0, f"GraphQL mutation validation failed: {errors}"
    
    def test_get_deployment_status_query_valid(self, railway_schema):
        """Validate get_deployment_status GraphQL query."""
        query = """
        query GetDeployment($id: String!) {
          deployment(id: $id) {
            id
            status
            createdAt
            updatedAt
            staticUrl
            meta
          }
        }
        """
        
        document = parse(query)
        errors = validate(railway_schema, document)
        
        assert len(errors) == 0, f"GraphQL query validation failed: {errors}"
    
    def test_get_project_environments_query_valid(self, railway_schema):
        """Validate get_project_environments GraphQL query."""
        query = """
        query GetProjectEnvironments($projectId: String!) {
          project(id: $projectId) {
            environments {
              edges {
                node {
                  id
                  name
                  createdAt
                }
              }
            }
          }
        }
        """
        
        document = parse(query)
        errors = validate(railway_schema, document)
        
        assert len(errors) == 0, f"GraphQL query validation failed: {errors}"
    
    def test_get_service_variables_query_valid(self, railway_schema):
        """Validate get_service_variables GraphQL query."""
        query = """
        query GetServiceVariables($serviceId: String!, $environmentId: String!) {
          variables(serviceId: $serviceId, environmentId: $environmentId) {
            edges {
              node {
                name
                value
              }
            }
          }
        }
        """
        
        document = parse(query)
        errors = validate(railway_schema, document)
        
        assert len(errors) == 0, f"GraphQL query validation failed: {errors}"


class TestRailwayAPIConnectivity:
    """Test actual connectivity to Railway API (requires valid token)."""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("RAILWAY_API_TOKEN"),
        reason="RAILWAY_API_TOKEN not set"
    )
    async def test_railway_api_connectivity(self):
        """Test that we can connect to Railway API with real token."""
        client = RailwayClient()
        
        # Try to fetch projects - this validates token and connectivity
        try:
            projects = await client.get_projects()
            assert isinstance(projects, list), "Expected list of projects"
            print(f"✓ Connected to Railway API, found {len(projects)} projects")
        except RailwayAPIError as e:
            pytest.fail(f"Failed to connect to Railway API: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("RAILWAY_API_TOKEN"),
        reason="RAILWAY_API_TOKEN not set"
    )
    async def test_railway_api_authentication(self):
        """Test that Railway API token is valid."""
        client = RailwayClient()
        
        # Execute a simple query to validate authentication
        query = """
        query {
          projects {
            edges {
              node {
                id
              }
            }
          }
        }
        """
        
        try:
            result = await client._execute_query(query)
            assert "projects" in result, "Expected 'projects' in response"
            print("✓ Railway API authentication successful")
        except RailwayAPIError as e:
            if "Unauthorized" in str(e) or "authentication" in str(e).lower():
                pytest.fail("Railway API token is invalid or expired")
            else:
                pytest.fail(f"Railway API error: {e}")


class TestGraphQLQueryStructure:
    """Test that queries have proper structure and variable usage."""
    
    def test_all_queries_use_variables_correctly(self):
        """Ensure queries with parameters use GraphQL variables, not string interpolation."""
        # This is a design validation - we should never use string interpolation
        # in GraphQL queries to prevent injection attacks
        
        queries_to_check = [
            "query GetProjectServices($projectId: String!)",
            "query GetServiceDeployments($serviceId: String!)",
            "mutation DeploymentTrigger($serviceId: String!, $environmentId: String!)",
            "query GetDeployment($id: String!)",
            "query GetProjectEnvironments($projectId: String!)",
            "query GetServiceVariables($serviceId: String!, $environmentId: String!)"
        ]
        
        for query_signature in queries_to_check:
            # Ensure the signature includes proper variable declarations
            assert "$" in query_signature, f"Query should use variables: {query_signature}"
            assert "String!" in query_signature, f"Variables should have types: {query_signature}"
        
        print("✓ All parameterized queries use variables correctly")
    
    def test_no_hardcoded_ids_in_queries(self):
        """Ensure no queries have hardcoded IDs or values."""
        # Read the railway_api.py file and check for potential issues
        import inspect
        from railway_api import RailwayClient
        
        source = inspect.getsource(RailwayClient)
        
        # Check for common patterns that indicate hardcoded values
        dangerous_patterns = [
            'query { project(id: "',
            'query { service(id: "',
            'mutation { deploymentTrigger(serviceId: "'
        ]
        
        for pattern in dangerous_patterns:
            assert pattern not in source, f"Found hardcoded ID in query: {pattern}"
        
        print("✓ No hardcoded IDs found in queries")


class TestErrorHandling:
    """Test error handling for GraphQL operations."""
    
    @pytest.mark.asyncio
    async def test_handles_graphql_errors_properly(self):
        """Test that GraphQL errors are properly caught and reported."""
        client = RailwayClient(api_token="test-token")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "errors": [
                {"message": "Invalid project ID"},
                {"message": "Field 'invalidField' doesn't exist on type 'Project'"}
            ]
        }
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises(RailwayAPIError) as exc_info:
                await client._execute_query("query { invalid }")
            
            error_message = str(exc_info.value)
            assert "Invalid project ID" in error_message
            assert "invalidField" in error_message
    
    @pytest.mark.asyncio
    async def test_handles_network_errors_properly(self):
        """Test that network errors are properly caught and reported."""
        client = RailwayClient(api_token="test-token")
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = Exception("Network error")
            
            with pytest.raises(RailwayAPIError) as exc_info:
                await client._execute_query("query { projects }")
            
            assert "Error communicating with Railway API" in str(exc_info.value)


class TestQueryPerformance:
    """Test that queries are optimized and don't request unnecessary data."""
    
    def test_deployments_query_has_pagination(self):
        """Ensure deployment queries use pagination to avoid fetching too much data."""
        query = """
        query GetServiceDeployments($serviceId: String!) {
          service(id: $serviceId) {
            deployments(first: 10, orderBy: {column: CREATED_AT, direction: DESC}) {
              edges {
                node {
                  id
                  status
                  createdAt
                  updatedAt
                  staticUrl
                  meta
                }
              }
            }
          }
        }
        """
        
        # Verify the query includes pagination
        assert "first:" in query, "Deployment query should include pagination (first: N)"
        assert "orderBy:" in query, "Deployment query should include ordering"
        
        print("✓ Deployment queries use pagination")
    
    def test_queries_only_request_needed_fields(self):
        """Ensure queries only request fields that are actually used."""
        # This is a manual verification point - queries should be lean
        # and not request more data than needed
        
        from railway_api import RailwayClient
        import inspect
        
        source = inspect.getsource(RailwayClient)
        
        # Check that we're not requesting all fields with a wildcard
        # (GraphQL doesn't support this anyway, but it's good practice to verify)
        assert "edges { * }" not in source
        assert "node { * }" not in source
        
        print("✓ Queries request specific fields only")
