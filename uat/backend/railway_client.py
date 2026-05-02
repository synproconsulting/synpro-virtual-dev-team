"""
Railway GraphQL API client for querying deployment information.

This module provides a client to interact with Railway's GraphQL API
to fetch project, service, and deployment information.
"""

import os
import logging
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class RailwayClient:
    """Client for interacting with Railway's GraphQL API."""
    
    RAILWAY_API_URL = "https://backboard.railway.app/graphql/v2"
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize Railway client.
        
        Args:
            api_token: Railway API token. If not provided, reads from RAILWAY_API_TOKEN env var.
        
        Raises:
            ValueError: If no API token is provided or found in environment.
        """
        self.api_token = api_token or os.environ.get("RAILWAY_API_TOKEN")
        if not self.api_token:
            raise ValueError("Railway API token is required. Set RAILWAY_API_TOKEN environment variable.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
    
    async def _execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against Railway API.
        
        Args:
            query: GraphQL query string.
            variables: Optional query variables.
        
        Returns:
            Response data from Railway API.
        
        Raises:
            httpx.HTTPError: If the request fails.
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.RAILWAY_API_URL,
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                error_messages = [err.get("message", str(err)) for err in data["errors"]]
                raise Exception(f"GraphQL errors: {', '.join(error_messages)}")
            
            return data.get("data", {})
    
    async def get_projects(self) -> List[Dict[str, Any]]:
        """
        Get all projects accessible to the user.
        
        Returns:
            List of project information dictionaries.
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
                        updatedAt
                    }
                }
            }
        }
        """
        
        try:
            data = await self._execute_query(query)
            projects = data.get("projects", {}).get("edges", [])
            return [edge["node"] for edge in projects]
        except Exception as e:
            logger.error(f"Failed to fetch projects: {e}")
            raise
    
    async def get_project_services(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all services in a project.
        
        Args:
            project_id: Railway project ID.
        
        Returns:
            List of service information dictionaries.
        """
        query = """
        query getProjectServices($projectId: String!) {
            project(id: $projectId) {
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
            }
        }
        """
        
        try:
            data = await self._execute_query(query, {"projectId": project_id})
            services = data.get("project", {}).get("services", {}).get("edges", [])
            return [edge["node"] for edge in services]
        except Exception as e:
            logger.error(f"Failed to fetch services for project {project_id}: {e}")
            raise
    
    async def get_service_deployments(
        self, 
        service_id: str, 
        environment_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent deployments for a service.
        
        Args:
            service_id: Railway service ID.
            environment_id: Optional environment ID to filter deployments.
            limit: Maximum number of deployments to return.
        
        Returns:
            List of deployment information dictionaries.
        """
        query = """
        query getServiceDeployments($serviceId: String!, $first: Int!) {
            service(id: $serviceId) {
                id
                name
                deployments(first: $first) {
                    edges {
                        node {
                            id
                            status
                            createdAt
                            updatedAt
                            staticUrl
                            meta
                            environmentId
                        }
                    }
                }
            }
        }
        """
        
        try:
            data = await self._execute_query(
                query, 
                {"serviceId": service_id, "first": limit}
            )
            deployments = data.get("service", {}).get("deployments", {}).get("edges", [])
            deployment_list = [edge["node"] for edge in deployments]
            
            # Filter by environment if specified
            if environment_id:
                deployment_list = [
                    d for d in deployment_list 
                    if d.get("environmentId") == environment_id
                ]
            
            return deployment_list
        except Exception as e:
            logger.error(f"Failed to fetch deployments for service {service_id}: {e}")
            raise
    
    async def get_deployment_logs(
        self, 
        deployment_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get logs for a specific deployment.
        
        Args:
            deployment_id: Railway deployment ID.
            limit: Maximum number of log entries to return.
        
        Returns:
            List of log entry dictionaries.
        """
        query = """
        query getDeploymentLogs($deploymentId: String!, $limit: Int!) {
            deploymentLogs(deploymentId: $deploymentId, limit: $limit) {
                id
                message
                timestamp
                severity
            }
        }
        """
        
        try:
            data = await self._execute_query(
                query,
                {"deploymentId": deployment_id, "limit": limit}
            )
            return data.get("deploymentLogs", [])
        except Exception as e:
            logger.error(f"Failed to fetch logs for deployment {deployment_id}: {e}")
            raise
    
    async def get_environment_deployments(
        self, 
        project_id: str,
        environment_name: str = "production"
    ) -> List[Dict[str, Any]]:
        """
        Get all deployments for all services in an environment.
        
        Args:
            project_id: Railway project ID.
            environment_name: Name of the environment (e.g., 'production', 'staging').
        
        Returns:
            List of deployment information with service details.
        """
        query = """
        query getEnvironmentDeployments($projectId: String!) {
            project(id: $projectId) {
                id
                name
                environments {
                    edges {
                        node {
                            id
                            name
                            deployments(first: 5) {
                                edges {
                                    node {
                                        id
                                        status
                                        createdAt
                                        updatedAt
                                        staticUrl
                                        serviceId
                                    }
                                }
                            }
                        }
                    }
                }
                services {
                    edges {
                        node {
                            id
                            name
                        }
                    }
                }
            }
        }
        """
        
        try:
            data = await self._execute_query(query, {"projectId": project_id})
            project_data = data.get("project", {})
            
            # Build service ID to name mapping
            services = project_data.get("services", {}).get("edges", [])
            service_map = {
                edge["node"]["id"]: edge["node"]["name"]
                for edge in services
            }
            
            # Find the target environment
            environments = project_data.get("environments", {}).get("edges", [])
            target_env = None
            for edge in environments:
                env = edge["node"]
                if env["name"].lower() == environment_name.lower():
                    target_env = env
                    break
            
            if not target_env:
                logger.warning(f"Environment '{environment_name}' not found in project {project_id}")
                return []
            
            # Extract deployments with service names
            deployments = target_env.get("deployments", {}).get("edges", [])
            result = []
            for edge in deployments:
                deployment = edge["node"]
                service_id = deployment.get("serviceId")
                deployment["serviceName"] = service_map.get(service_id, "Unknown Service")
                result.append(deployment)
            
            return result
        except Exception as e:
            logger.error(f"Failed to fetch environment deployments: {e}")
            raise
    
    async def trigger_deployment(
        self,
        service_id: str,
        environment_id: str
    ) -> Dict[str, Any]:
        """
        Trigger a new deployment for a service.
        
        Args:
            service_id: Railway service ID.
            environment_id: Railway environment ID.
        
        Returns:
            Deployment information.
        """
        mutation = """
        mutation deployService($serviceId: String!, $environmentId: String!) {
            serviceDeploy(serviceId: $serviceId, environmentId: $environmentId) {
                id
                status
                createdAt
            }
        }
        """
        
        try:
            data = await self._execute_query(
                mutation,
                {"serviceId": service_id, "environmentId": environment_id}
            )
            return data.get("serviceDeploy", {})
        except Exception as e:
            logger.error(f"Failed to trigger deployment for service {service_id}: {e}")
            raise


def get_railway_client() -> RailwayClient:
    """
    Factory function to create a Railway client instance.
    
    Returns:
        Configured RailwayClient instance.
    
    Raises:
        ValueError: If Railway API token is not configured.
    """
    return RailwayClient()
