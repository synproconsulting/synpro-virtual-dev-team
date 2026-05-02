"""
Railway GraphQL Deployment Validator

This module provides validation and health checking for Railway deployments
via the Railway GraphQL API.
"""

import os
import json
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import requests


class DeploymentStatus(Enum):
    """Railway deployment status enum."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    BUILDING = "BUILDING"
    DEPLOYING = "DEPLOYING"
    CRASHED = "CRASHED"
    REMOVED = "REMOVED"
    UNKNOWN = "UNKNOWN"


@dataclass
class ValidationResult:
    """Result of a deployment validation check."""
    success: bool
    message: str
    deployment_id: Optional[str] = None
    status: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


class RailwayDeployValidator:
    """Validates Railway deployments via GraphQL API."""
    
    GRAPHQL_ENDPOINT = "https://backboard.railway.app/graphql/v2"
    
    def __init__(self, railway_token: str, project_id: str):
        """
        Initialize Railway deployment validator.
        
        Args:
            railway_token: Railway API authentication token
            project_id: Railway project ID
        """
        self.railway_token = railway_token
        self.project_id = project_id
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {railway_token}",
            "Content-Type": "application/json"
        })
    
    def _execute_graphql_query(self, query: str) -> Dict[str, Any]:
        """
        Execute a GraphQL query against Railway API.
        
        Args:
            query: GraphQL query string
            
        Returns:
            Response data dictionary
            
        Raises:
            requests.exceptions.RequestException: On API failure
        """
        payload = {"query": query}
        response = self.session.post(
            self.GRAPHQL_ENDPOINT,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            raise ValueError(f"GraphQL errors: {json.dumps(data['errors'])}")
        
        return data
    
    def get_project_info(self) -> Dict[str, Any]:
        """
        Retrieve project information including services and environments.
        
        Returns:
            Project information dictionary
        """
        query = f"""
        {{
          project(id: "{self.project_id}") {{
            id
            name
            environments {{
              edges {{
                node {{
                  id
                  name
                }}
              }}
            }}
            services {{
              edges {{
                node {{
                  id
                  name
                }}
              }}
            }}
          }}
        }}
        """
        
        result = self._execute_graphql_query(query)
        return result.get("data", {}).get("project", {})
    
    def get_service_deployments(
        self,
        service_id: str,
        environment_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recent deployments for a service in an environment.
        
        Args:
            service_id: Service ID
            environment_id: Environment ID
            limit: Maximum number of deployments to retrieve
            
        Returns:
            List of deployment dictionaries
        """
        query = f"""
        {{
          deployments(
            input: {{
              environmentId: "{environment_id}"
              serviceId: "{service_id}"
            }}
            first: {limit}
          ) {{
            edges {{
              node {{
                id
                status
                createdAt
                updatedAt
                canRedeploy
                meta
              }}
            }}
          }}
        }}
        """
        
        result = self._execute_graphql_query(query)
        edges = result.get("data", {}).get("deployments", {}).get("edges", [])
        return [edge["node"] for edge in edges]
    
    def resolve_service_and_environment(
        self,
        service_name: str,
        environment_name: str = "production"
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Resolve service and environment IDs from their names.
        
        Args:
            service_name: Name of the service
            environment_name: Name of the environment (default: production)
            
        Returns:
            Tuple of (service_id, environment_id) or (None, None) if not found
        """
        try:
            project_info = self.get_project_info()
            
            # Find environment ID
            env_id = None
            for edge in project_info.get("environments", {}).get("edges", []):
                node = edge.get("node", {})
                if node.get("name", "").lower() == environment_name.lower():
                    env_id = node.get("id")
                    break
            
            # Find service ID
            svc_id = None
            for edge in project_info.get("services", {}).get("edges", []):
                node = edge.get("node", {})
                if node.get("name") == service_name:
                    svc_id = node.get("id")
                    break
            
            return svc_id, env_id
            
        except Exception as e:
            print(f"Error resolving service/environment: {e}")
            return None, None
    
    def trigger_redeploy(
        self,
        service_id: str,
        environment_id: str
    ) -> ValidationResult:
        """
        Trigger a service redeploy via GraphQL mutation.
        
        Args:
            service_id: Service ID
            environment_id: Environment ID
            
        Returns:
            ValidationResult indicating success or failure
        """
        mutation = f"""
        mutation {{
          serviceInstanceRedeploy(
            environmentId: "{environment_id}"
            serviceId: "{service_id}"
          )
        }}
        """
        
        try:
            result = self._execute_graphql_query(mutation)
            redeploy_result = result.get("data", {}).get("serviceInstanceRedeploy")
            
            if redeploy_result:
                return ValidationResult(
                    success=True,
                    message="Redeploy triggered successfully",
                    deployment_id=str(redeploy_result)
                )
            else:
                return ValidationResult(
                    success=False,
                    message="Redeploy mutation returned no result"
                )
                
        except Exception as e:
            return ValidationResult(
                success=False,
                message=f"Failed to trigger redeploy: {str(e)}",
                error_details={"exception": str(e)}
            )
    
    def validate_deployment_status(
        self,
        service_id: str,
        environment_id: str,
        timeout_seconds: int = 300,
        check_interval: int = 10
    ) -> ValidationResult:
        """
        Validate deployment status with polling until success or timeout.
        
        Args:
            service_id: Service ID
            environment_id: Environment ID
            timeout_seconds: Maximum time to wait for deployment
            check_interval: Seconds between status checks
            
        Returns:
            ValidationResult with final deployment status
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            try:
                deployments = self.get_service_deployments(
                    service_id,
                    environment_id,
                    limit=1
                )
                
                if not deployments:
                    return ValidationResult(
                        success=False,
                        message="No deployments found for service"
                    )
                
                latest = deployments[0]
                status = latest.get("status", "UNKNOWN")
                deployment_id = latest.get("id")
                
                # Check for terminal states
                if status in ["SUCCESS", "READY"]:
                    return ValidationResult(
                        success=True,
                        message=f"Deployment {deployment_id} succeeded",
                        deployment_id=deployment_id,
                        status=status
                    )
                
                if status in ["FAILED", "CRASHED"]:
                    return ValidationResult(
                        success=False,
                        message=f"Deployment {deployment_id} failed with status: {status}",
                        deployment_id=deployment_id,
                        status=status,
                        error_details=latest.get("meta", {})
                    )
                
                # Still in progress
                print(f"Deployment {deployment_id} status: {status}, waiting...")
                time.sleep(check_interval)
                
            except Exception as e:
                return ValidationResult(
                    success=False,
                    message=f"Error checking deployment status: {str(e)}",
                    error_details={"exception": str(e)}
                )
        
        return ValidationResult(
            success=False,
            message=f"Deployment validation timed out after {timeout_seconds}s"
        )
    
    def validate_api_connectivity(self) -> ValidationResult:
        """
        Validate that we can connect to Railway API with provided credentials.
        
        Returns:
            ValidationResult indicating API connectivity status
        """
        try:
            project_info = self.get_project_info()
            
            if not project_info:
                return ValidationResult(
                    success=False,
                    message="Failed to retrieve project information"
                )
            
            project_name = project_info.get("name", "unknown")
            service_count = len(
                project_info.get("services", {}).get("edges", [])
            )
            env_count = len(
                project_info.get("environments", {}).get("edges", [])
            )
            
            return ValidationResult(
                success=True,
                message=(
                    f"Railway API connectivity validated. "
                    f"Project: {project_name}, "
                    f"Services: {service_count}, "
                    f"Environments: {env_count}"
                )
            )
            
        except requests.exceptions.RequestException as e:
            return ValidationResult(
                success=False,
                message=f"Railway API connectivity check failed: {str(e)}",
                error_details={"exception": str(e)}
            )
        except Exception as e:
            return ValidationResult(
                success=False,
                message=f"Unexpected error during connectivity check: {str(e)}",
                error_details={"exception": str(e)}
            )


def main() -> int:
    """
    Main entry point for standalone validation script.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    railway_token = os.getenv("RAILWAY_TOKEN")
    project_id = os.getenv("RAILWAY_PROJECT_ID")
    
    if not railway_token or not project_id:
        print("ERROR: RAILWAY_TOKEN and RAILWAY_PROJECT_ID must be set")
        return 1
    
    validator = RailwayDeployValidator(railway_token, project_id)
    
    # Step 1: Validate API connectivity
    print("=== Validating Railway API connectivity ===")
    connectivity_result = validator.validate_api_connectivity()
    print(f"Result: {connectivity_result.message}")
    
    if not connectivity_result.success:
        print("FAILED: Cannot connect to Railway API")
        if connectivity_result.error_details:
            print(f"Details: {json.dumps(connectivity_result.error_details, indent=2)}")
        return 1
    
    # Step 2: List all services and environments
    print("\n=== Listing project resources ===")
    project_info = validator.get_project_info()
    
    print("\nEnvironments:")
    for edge in project_info.get("environments", {}).get("edges", []):
        node = edge.get("node", {})
        print(f"  - {node.get('name')} (ID: {node.get('id')})")
    
    print("\nServices:")
    for edge in project_info.get("services", {}).get("edges", []):
        node = edge.get("node", {})
        print(f"  - {node.get('name')} (ID: {node.get('id')})")
    
    print("\n=== Validation complete ===")
    return 0


if __name__ == "__main__":
    exit(main())
