"""
backend/railway_client.py
═════════════════════════
Client for interacting with Railway GraphQL API.
Implements SDT1-58: UAT Deploy tab - wire to Railway GraphQL API
"""

import os
import logging
from typing import Optional, Dict, List, Any
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class RailwayAPIError(Exception):
    """Raised when Railway API returns an error."""
    pass


class RailwayClient:
    """
    Client for Railway GraphQL API.
    
    Provides methods to:
    - Get project information
    - List services and deployments
    - Trigger new deployments
    - Query deployment status
    """
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize Railway client.
        
        Args:
            api_token: Railway API token. If not provided, reads from RAILWAY_API_TOKEN env var.
            
        Raises:
            ValueError: If no API token is provided
        """
        self.api_token = api_token or os.environ.get("RAILWAY_API_TOKEN")
        if not self.api_token:
            raise ValueError(
                "Railway API token is required. Set RAILWAY_API_TOKEN environment variable "
                "or pass api_token parameter."
            )
        
        self.api_url = "https://backboard.railway.app/graphql/v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
    
    async def _execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against Railway API.
        
        Args:
            query: GraphQL query string
            variables: Query variables
            
        Returns:
            Query response data
            
        Raises:
            RailwayAPIError: If the API returns an error
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Check for GraphQL errors
                if "errors" in data:
                    error_messages = [err.get("message", str(err)) for err in data["errors"]]
                    raise RailwayAPIError(f"GraphQL errors: {'; '.join(error_messages)}")
                
                return data.get("data", {})
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Railway API HTTP error: {e}")
                raise RailwayAPIError(f"Railway API request failed: {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"Railway API request error: {e}")
                raise RailwayAPIError(f"Failed to connect to Railway API: {str(e)}")
    
    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get project information by ID.
        
        Args:
            project_id: Railway project ID
            
        Returns:
            Project data including services and environments
        """
        query = """
        query GetProject($projectId: String!) {
            project(id: $projectId) {
                id
                name
                description
                createdAt
                updatedAt
                services {
                    edges {
                        node {
                            id
                            name
                            createdAt
                            updatedAt
                        }
                    }
                }
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
        
        result = await self._execute_query(query, {"projectId": project_id})
        return result.get("project", {})
    
    async def get_service_deployments(
        self,
        service_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get deployments for a specific service.
        
        Args:
            service_id: Railway service ID
            limit: Maximum number of deployments to return
            
        Returns:
            List of deployment records
        """
        query = """
        query GetServiceDeployments($serviceId: String!, $first: Int) {
            deployments(input: {serviceId: $serviceId}, first: $first) {
                edges {
                    node {
                        id
                        status
                        createdAt
                        updatedAt
                        staticUrl
                        meta
                        environment {
                            id
                            name
                        }
                        canRollback
                        canRedeploy
                    }
                }
            }
        }
        """
        
        result = await self._execute_query(
            query,
            {"serviceId": service_id, "first": limit}
        )
        
        deployments = result.get("deployments", {}).get("edges", [])
        return [edge["node"] for edge in deployments]
    
    async def trigger_deployment(
        self,
        service_id: str,
        environment_id: str,
        use_custom_branch: bool = False,
        custom_branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trigger a new deployment for a service.
        
        Args:
            service_id: Railway service ID
            environment_id: Railway environment ID
            use_custom_branch: Whether to deploy from a custom branch
            custom_branch: Custom branch name (required if use_custom_branch is True)
            
        Returns:
            Deployment record
            
        Raises:
            RailwayAPIError: If deployment fails to trigger
        """
        mutation = """
        mutation DeployService($serviceId: String!, $environmentId: String!) {
            serviceDeploy(input: {serviceId: $serviceId, environmentId: $environmentId}) {
                id
                status
                createdAt
                staticUrl
            }
        }
        """
        
        # Note: Custom branch deployment requires different mutation
        # Railway API typically uses serviceInstanceRedeploy for redeployments
        # with different configurations
        
        variables = {
            "serviceId": service_id,
            "environmentId": environment_id,
        }
        
        result = await self._execute_query(mutation, variables)
        
        deployment = result.get("serviceDeploy")
        if not deployment:
            raise RailwayAPIError("Failed to trigger deployment: No deployment data returned")
        
        logger.info(f"Triggered deployment {deployment['id']} for service {service_id}")
        return deployment
    
    async def get_deployment_logs(
        self,
        deployment_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get logs for a specific deployment.
        
        Args:
            deployment_id: Railway deployment ID
            limit: Maximum number of log entries to return
            
        Returns:
            List of log entries
        """
        query = """
        query GetDeploymentLogs($deploymentId: String!, $limit: Int) {
            deploymentLogs(deploymentId: $deploymentId, limit: $limit) {
                edges {
                    node {
                        timestamp
                        message
                        severity
                    }
                }
            }
        }
        """
        
        result = await self._execute_query(
            query,
            {"deploymentId": deployment_id, "limit": limit}
        )
        
        logs = result.get("deploymentLogs", {}).get("edges", [])
        return [edge["node"] for edge in logs]
    
    async def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """
        Get the current status of a deployment.
        
        Args:
            deployment_id: Railway deployment ID
            
        Returns:
            Deployment status information
        """
        query = """
        query GetDeployment($deploymentId: String!) {
            deployment(id: $deploymentId) {
                id
                status
                createdAt
                updatedAt
                staticUrl
                meta
                canRollback
                canRedeploy
                environment {
                    id
                    name
                }
                service {
                    id
                    name
                }
            }
        }
        """
        
        result = await self._execute_query(query, {"deploymentId": deployment_id})
        return result.get("deployment", {})
    
    async def list_services(self, project_id: str) -> List[Dict[str, Any]]:
        """
        List all services in a project.
        
        Args:
            project_id: Railway project ID
            
        Returns:
            List of service records
        """
        query = """
        query ListServices($projectId: String!) {
            project(id: $projectId) {
                services {
                    edges {
                        node {
                            id
                            name
                            createdAt
                            updatedAt
                            icon
                        }
                    }
                }
            }
        }
        """
        
        result = await self._execute_query(query, {"projectId": project_id})
        
        services = result.get("project", {}).get("services", {}).get("edges", [])
        return [edge["node"] for edge in services]
    
    async def get_environments(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all environments for a project.
        
        Args:
            project_id: Railway project ID
            
        Returns:
            List of environment records
        """
        query = """
        query GetEnvironments($projectId: String!) {
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
        
        result = await self._execute_query(query, {"projectId": project_id})
        
        environments = result.get("project", {}).get("environments", {}).get("edges", [])
        return [edge["node"] for edge in environments]


def get_railway_client() -> RailwayClient:
    """
    Get a Railway client instance.
    
    Returns:
        Configured RailwayClient instance
        
    Raises:
        ValueError: If RAILWAY_API_TOKEN is not set
    """
    return RailwayClient()
