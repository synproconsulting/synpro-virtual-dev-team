"""
Railway GraphQL API client.
Handles communication with Railway's GraphQL API for deployments.
"""

import os
import logging
from typing import Dict, List, Optional, Any
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class RailwayClientError(Exception):
    """Raised when Railway API operations fail."""
    pass


class RailwayDeployment(BaseModel):
    """Model for Railway deployment information."""
    id: str
    status: str
    environment_name: str
    service_name: str
    created_at: str
    url: Optional[str] = None


class RailwayService(BaseModel):
    """Model for Railway service information."""
    id: str
    name: str
    icon: Optional[str] = None
    created_at: str


class RailwayEnvironment(BaseModel):
    """Model for Railway environment information."""
    id: str
    name: str
    service_instances: List[Dict[str, Any]] = []


class RailwayClient:
    """
    Client for interacting with Railway GraphQL API.
    
    Environment variables:
        RAILWAY_API_TOKEN: Railway API token (required)
        RAILWAY_PROJECT_ID: Railway project ID (required)
        RAILWAY_ENVIRONMENT_ID: Railway environment ID (optional, for UAT)
    """
    
    GRAPHQL_ENDPOINT = "https://backboard.railway.app/graphql/v2"
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        project_id: Optional[str] = None,
        environment_id: Optional[str] = None,
    ):
        """
        Initialize Railway client.
        
        Args:
            api_token: Railway API token (defaults to RAILWAY_API_TOKEN env var)
            project_id: Railway project ID (defaults to RAILWAY_PROJECT_ID env var)
            environment_id: Railway environment ID (defaults to RAILWAY_ENVIRONMENT_ID env var)
        """
        self.api_token = api_token or os.environ.get("RAILWAY_API_TOKEN", "")
        self.project_id = project_id or os.environ.get("RAILWAY_PROJECT_ID", "")
        self.environment_id = environment_id or os.environ.get("RAILWAY_ENVIRONMENT_ID", "")
        
        if not self.api_token:
            raise RailwayClientError("RAILWAY_API_TOKEN environment variable is required")
        if not self.project_id:
            raise RailwayClientError("RAILWAY_PROJECT_ID environment variable is required")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
    
    async def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """
        Execute a GraphQL query against Railway API.
        
        Args:
            query: GraphQL query string
            variables: Query variables
            
        Returns:
            GraphQL response data
            
        Raises:
            RailwayClientError: If the query fails
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.GRAPHQL_ENDPOINT,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0,
                )
                response.raise_for_status()
                
                data = response.json()
                
                if "errors" in data:
                    error_msg = "; ".join([e.get("message", str(e)) for e in data["errors"]])
                    raise RailwayClientError(f"GraphQL errors: {error_msg}")
                
                return data.get("data", {})
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error calling Railway API: {e}")
                raise RailwayClientError(f"HTTP error: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error calling Railway API: {e}")
                raise RailwayClientError(f"Unexpected error: {str(e)}")
    
    async def get_project_info(self) -> Dict:
        """
        Get project information.
        
        Returns:
            Project information including environments and services
        """
        query = """
        query GetProject($projectId: String!) {
            project(id: $projectId) {
                id
                name
                description
                createdAt
                environments {
                    edges {
                        node {
                            id
                            name
                            serviceInstances {
                                edges {
                                    node {
                                        id
                                        serviceId
                                        latestDeployment {
                                            id
                                            status
                                            createdAt
                                        }
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
                            icon
                            createdAt
                        }
                    }
                }
            }
        }
        """
        
        variables = {"projectId": self.project_id}
        result = await self._execute_query(query, variables)
        return result.get("project", {})
    
    async def list_services(self) -> List[RailwayService]:
        """
        List all services in the project.
        
        Returns:
            List of Railway services
        """
        project_info = await self.get_project_info()
        services = []
        
        for edge in project_info.get("services", {}).get("edges", []):
            node = edge.get("node", {})
            services.append(RailwayService(
                id=node.get("id", ""),
                name=node.get("name", ""),
                icon=node.get("icon"),
                created_at=node.get("createdAt", ""),
            ))
        
        return services
    
    async def list_environments(self) -> List[RailwayEnvironment]:
        """
        List all environments in the project.
        
        Returns:
            List of Railway environments
        """
        project_info = await self.get_project_info()
        environments = []
        
        for edge in project_info.get("environments", {}).get("edges", []):
            node = edge.get("node", {})
            service_instances = []
            
            for si_edge in node.get("serviceInstances", {}).get("edges", []):
                service_instances.append(si_edge.get("node", {}))
            
            environments.append(RailwayEnvironment(
                id=node.get("id", ""),
                name=node.get("name", ""),
                service_instances=service_instances,
            ))
        
        return environments
    
    async def trigger_deployment(
        self,
        service_id: str,
        environment_id: Optional[str] = None,
    ) -> str:
        """
        Trigger a new deployment for a service.
        
        Args:
            service_id: Railway service ID
            environment_id: Environment ID (defaults to configured environment)
            
        Returns:
            Deployment ID
            
        Raises:
            RailwayClientError: If deployment trigger fails
        """
        env_id = environment_id or self.environment_id
        if not env_id:
            raise RailwayClientError(
                "Environment ID is required. Set RAILWAY_ENVIRONMENT_ID or pass environment_id parameter."
            )
        
        mutation = """
        mutation DeploymentTrigger($environmentId: String!, $serviceId: String!) {
            deploymentTrigger(
                input: {
                    environmentId: $environmentId
                    serviceId: $serviceId
                }
            ) {
                id
                status
                createdAt
            }
        }
        """
        
        variables = {
            "environmentId": env_id,
            "serviceId": service_id,
        }
        
        result = await self._execute_query(mutation, variables)
        deployment_trigger = result.get("deploymentTrigger", {})
        
        if not deployment_trigger:
            raise RailwayClientError("Deployment trigger returned empty response")
        
        deployment_id = deployment_trigger.get("id", "")
        logger.info(f"Triggered deployment {deployment_id} for service {service_id}")
        
        return deployment_id
    
    async def get_deployment_status(self, deployment_id: str) -> RailwayDeployment:
        """
        Get the status of a deployment.
        
        Args:
            deployment_id: Railway deployment ID
            
        Returns:
            Deployment information
        """
        query = """
        query GetDeployment($deploymentId: String!) {
            deployment(id: $deploymentId) {
                id
                status
                createdAt
                environment {
                    name
                }
                service {
                    name
                }
                url
            }
        }
        """
        
        variables = {"deploymentId": deployment_id}
        result = await self._execute_query(query, variables)
        deployment = result.get("deployment", {})
        
        if not deployment:
            raise RailwayClientError(f"Deployment {deployment_id} not found")
        
        return RailwayDeployment(
            id=deployment.get("id", ""),
            status=deployment.get("status", ""),
            environment_name=deployment.get("environment", {}).get("name", ""),
            service_name=deployment.get("service", {}).get("name", ""),
            created_at=deployment.get("createdAt", ""),
            url=deployment.get("url"),
        )
    
    async def list_deployments(
        self,
        service_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[RailwayDeployment]:
        """
        List recent deployments.
        
        Args:
            service_id: Filter by service ID (optional)
            limit: Maximum number of deployments to return
            
        Returns:
            List of deployments
        """
        # Note: Railway API doesn't have a direct "list deployments" query
        # We need to get deployments through services or project info
        project_info = await self.get_project_info()
        deployments = []
        
        for env_edge in project_info.get("environments", {}).get("edges", []):
            env_node = env_edge.get("node", {})
            env_name = env_node.get("name", "")
            
            for si_edge in env_node.get("serviceInstances", {}).get("edges", []):
                si_node = si_edge.get("node", {})
                
                # Filter by service_id if provided
                if service_id and si_node.get("serviceId") != service_id:
                    continue
                
                latest_deployment = si_node.get("latestDeployment")
                if latest_deployment:
                    # Get full deployment details
                    try:
                        deployment = await self.get_deployment_status(latest_deployment.get("id", ""))
                        deployments.append(deployment)
                    except Exception as e:
                        logger.warning(f"Failed to fetch deployment details: {e}")
                        continue
        
        # Sort by creation date (newest first) and limit
        deployments.sort(key=lambda d: d.created_at, reverse=True)
        return deployments[:limit]
    
    async def get_service_logs(
        self,
        deployment_id: str,
        limit: int = 100,
    ) -> List[str]:
        """
        Get logs for a deployment.
        
        Args:
            deployment_id: Railway deployment ID
            limit: Maximum number of log lines to return
            
        Returns:
            List of log lines
        """
        query = """
        query GetDeploymentLogs($deploymentId: String!, $limit: Int) {
            deploymentLogs(deploymentId: $deploymentId, limit: $limit) {
                message
                timestamp
            }
        }
        """
        
        variables = {
            "deploymentId": deployment_id,
            "limit": limit,
        }
        
        result = await self._execute_query(query, variables)
        logs = result.get("deploymentLogs", [])
        
        return [log.get("message", "") for log in logs]
