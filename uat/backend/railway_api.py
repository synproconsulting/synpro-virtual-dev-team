"""
railway_api.py
==============
Railway GraphQL API client for deployment operations.
Handles authentication and GraphQL queries/mutations to Railway platform.
"""

import os
import logging
from typing import Dict, List, Optional, Any
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class RailwayAPIError(Exception):
    """Exception raised for Railway API errors."""
    pass


class RailwayClient:
    """
    Client for interacting with Railway GraphQL API.
    
    Documentation: https://docs.railway.app/reference/public-api
    """
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize Railway API client.
        
        Args:
            api_token: Railway API token. If not provided, reads from RAILWAY_API_TOKEN env var.
        
        Raises:
            RailwayAPIError: If API token is not provided or found in environment.
        """
        self.api_token = api_token or os.environ.get("RAILWAY_API_TOKEN")
        if not self.api_token:
            raise RailwayAPIError("Railway API token not provided")
        
        self.base_url = "https://backboard.railway.app/graphql/v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
    
    async def _execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against Railway API.
        
        Args:
            query: GraphQL query string
            variables: Optional variables for the query
            
        Returns:
            Response data from the GraphQL API
            
        Raises:
            RailwayAPIError: If the API request fails
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                
                if "errors" in data:
                    error_messages = [e.get("message", "Unknown error") for e in data["errors"]]
                    raise RailwayAPIError(f"GraphQL errors: {'; '.join(error_messages)}")
                
                return data.get("data", {})
        
        except httpx.HTTPError as e:
            logger.error(f"Railway API HTTP error: {e}")
            raise RailwayAPIError(f"HTTP error communicating with Railway API: {str(e)}")
        except Exception as e:
            logger.error(f"Railway API error: {e}")
            raise RailwayAPIError(f"Error communicating with Railway API: {str(e)}")
    
    async def get_projects(self) -> List[Dict[str, Any]]:
        """
        Get all projects accessible by the authenticated user.
        
        Returns:
            List of project objects with id, name, description, and createdAt
        """
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
        
        result = await self._execute_query(query)
        edges = result.get("projects", {}).get("edges", [])
        return [edge["node"] for edge in edges]
    
    async def get_project_services(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all services for a specific project.
        
        Args:
            project_id: Railway project ID
            
        Returns:
            List of service objects with id, name, and icon
        """
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
        
        variables = {"projectId": project_id}
        result = await self._execute_query(query, variables)
        edges = result.get("project", {}).get("services", {}).get("edges", [])
        return [edge["node"] for edge in edges]
    
    async def get_service_deployments(
        self, 
        service_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent deployments for a service.
        
        Args:
            service_id: Railway service ID
            limit: Maximum number of deployments to return
            
        Returns:
            List of deployment objects with status, createdAt, and metadata
        """
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
        
        variables = {"serviceId": service_id}
        result = await self._execute_query(query, variables)
        edges = result.get("service", {}).get("deployments", {}).get("edges", [])
        deployments = [edge["node"] for edge in edges]
        return deployments[:limit]
    
    async def trigger_deployment(
        self, 
        service_id: str, 
        environment_id: str
    ) -> Dict[str, Any]:
        """
        Trigger a new deployment for a service in a specific environment.
        
        Args:
            service_id: Railway service ID
            environment_id: Railway environment ID
            
        Returns:
            Deployment object with id, status, and metadata
        """
        mutation = """
        mutation DeploymentTrigger($serviceId: String!, $environmentId: String!) {
          deploymentTrigger(serviceId: $serviceId, environmentId: $environmentId) {
            id
            status
            createdAt
          }
        }
        """
        
        variables = {
            "serviceId": service_id,
            "environmentId": environment_id
        }
        
        result = await self._execute_query(mutation, variables)
        deployment = result.get("deploymentTrigger", {})
        
        if not deployment:
            raise RailwayAPIError("Deployment trigger returned no data")
        
        logger.info(f"Triggered deployment {deployment.get('id')} for service {service_id}")
        return deployment
    
    async def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """
        Get the current status of a deployment.
        
        Args:
            deployment_id: Railway deployment ID
            
        Returns:
            Deployment object with current status and metadata
        """
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
        
        variables = {"id": deployment_id}
        result = await self._execute_query(query, variables)
        deployment = result.get("deployment", {})
        
        if not deployment:
            raise RailwayAPIError(f"Deployment {deployment_id} not found")
        
        return deployment
    
    async def get_project_environments(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all environments for a project.
        
        Args:
            project_id: Railway project ID
            
        Returns:
            List of environment objects with id and name
        """
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
        
        variables = {"projectId": project_id}
        result = await self._execute_query(query, variables)
        edges = result.get("project", {}).get("environments", {}).get("edges", [])
        return [edge["node"] for edge in edges]
    
    async def get_service_variables(
        self, 
        service_id: str, 
        environment_id: str
    ) -> Dict[str, str]:
        """
        Get environment variables for a service in a specific environment.
        
        Args:
            service_id: Railway service ID
            environment_id: Railway environment ID
            
        Returns:
            Dictionary of environment variable key-value pairs
        """
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
        
        variables = {
            "serviceId": service_id,
            "environmentId": environment_id
        }
        
        result = await self._execute_query(query, variables)
        edges = result.get("variables", {}).get("edges", [])
        
        return {edge["node"]["name"]: edge["node"]["value"] for edge in edges}


async def get_railway_client() -> RailwayClient:
    """
    Factory function to create a Railway client instance.
    
    Returns:
        Configured RailwayClient instance
        
    Raises:
        RailwayAPIError: If Railway API token is not configured
    """
    return RailwayClient()
