"""
Railway deployment API router.

Provides endpoints for fetching Railway deployment status and triggering deployments.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from railway_client import get_railway_client, RailwayClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/railway", tags=["railway"])


class DeploymentTriggerRequest(BaseModel):
    """Request model for triggering a deployment."""
    
    service_id: str = Field(..., description="Railway service ID")
    environment_id: str = Field(..., description="Railway environment ID")


class DeploymentResponse(BaseModel):
    """Response model for deployment information."""
    
    id: str
    status: str
    service_name: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    static_url: Optional[str] = None


@router.get("/projects")
async def get_projects():
    """
    Get all Railway projects accessible to the configured API token.
    
    Returns:
        List of projects with basic information.
    """
    try:
        client = get_railway_client()
        projects = await client.get_projects()
        return {"projects": projects}
    except ValueError as e:
        logger.error(f"Railway client configuration error: {e}")
        raise HTTPException(status_code=500, detail="Railway API not configured")
    except Exception as e:
        logger.error(f"Failed to fetch projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")


@router.get("/projects/{project_id}/services")
async def get_project_services(project_id: str):
    """
    Get all services in a Railway project.
    
    Args:
        project_id: Railway project ID.
    
    Returns:
        List of services in the project.
    """
    try:
        client = get_railway_client()
        services = await client.get_project_services(project_id)
        return {"services": services}
    except ValueError as e:
        logger.error(f"Railway client configuration error: {e}")
        raise HTTPException(status_code=500, detail="Railway API not configured")
    except Exception as e:
        logger.error(f"Failed to fetch services: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch services: {str(e)}")


@router.get("/services/{service_id}/deployments")
async def get_service_deployments(
    service_id: str,
    environment_id: Optional[str] = Query(None, description="Filter by environment ID"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of deployments to return")
):
    """
    Get recent deployments for a service.
    
    Args:
        service_id: Railway service ID.
        environment_id: Optional environment ID to filter deployments.
        limit: Maximum number of deployments to return (1-50).
    
    Returns:
        List of recent deployments for the service.
    """
    try:
        client = get_railway_client()
        deployments = await client.get_service_deployments(
            service_id=service_id,
            environment_id=environment_id,
            limit=limit
        )
        return {"deployments": deployments}
    except ValueError as e:
        logger.error(f"Railway client configuration error: {e}")
        raise HTTPException(status_code=500, detail="Railway API not configured")
    except Exception as e:
        logger.error(f"Failed to fetch deployments: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch deployments: {str(e)}")


@router.get("/projects/{project_id}/environments/{environment_name}/deployments")
async def get_environment_deployments(
    project_id: str,
    environment_name: str = "production"
):
    """
    Get all deployments for all services in a specific environment.
    
    Args:
        project_id: Railway project ID.
        environment_name: Name of the environment (e.g., 'production', 'staging', 'uat').
    
    Returns:
        List of deployments in the environment with service information.
    """
    try:
        client = get_railway_client()
        deployments = await client.get_environment_deployments(
            project_id=project_id,
            environment_name=environment_name
        )
        return {
            "environment": environment_name,
            "deployments": deployments
        }
    except ValueError as e:
        logger.error(f"Railway client configuration error: {e}")
        raise HTTPException(status_code=500, detail="Railway API not configured")
    except Exception as e:
        logger.error(f"Failed to fetch environment deployments: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch environment deployments: {str(e)}"
        )


@router.get("/deployments/{deployment_id}/logs")
async def get_deployment_logs(
    deployment_id: str,
    limit: int = Query(100, ge=1, le=500, description="Maximum number of log entries")
):
    """
    Get logs for a specific deployment.
    
    Args:
        deployment_id: Railway deployment ID.
        limit: Maximum number of log entries to return (1-500).
    
    Returns:
        List of log entries for the deployment.
    """
    try:
        client = get_railway_client()
        logs = await client.get_deployment_logs(
            deployment_id=deployment_id,
            limit=limit
        )
        return {"logs": logs}
    except ValueError as e:
        logger.error(f"Railway client configuration error: {e}")
        raise HTTPException(status_code=500, detail="Railway API not configured")
    except Exception as e:
        logger.error(f"Failed to fetch deployment logs: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch deployment logs: {str(e)}"
        )


@router.post("/deployments/trigger")
async def trigger_deployment(request: DeploymentTriggerRequest):
    """
    Trigger a new deployment for a service.
    
    Args:
        request: Deployment trigger request with service and environment IDs.
    
    Returns:
        Information about the triggered deployment.
    """
    try:
        client = get_railway_client()
        deployment = await client.trigger_deployment(
            service_id=request.service_id,
            environment_id=request.environment_id
        )
        return {
            "success": True,
            "deployment": deployment,
            "message": "Deployment triggered successfully"
        }
    except ValueError as e:
        logger.error(f"Railway client configuration error: {e}")
        raise HTTPException(status_code=500, detail="Railway API not configured")
    except Exception as e:
        logger.error(f"Failed to trigger deployment: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to trigger deployment: {str(e)}"
        )


@router.get("/health")
async def railway_health_check():
    """
    Check if Railway API is configured and accessible.
    
    Returns:
        Health status of Railway integration.
    """
    try:
        client = get_railway_client()
        # Try to fetch projects as a health check
        projects = await client.get_projects()
        return {
            "status": "healthy",
            "configured": True,
            "projects_count": len(projects)
        }
    except ValueError:
        return {
            "status": "unconfigured",
            "configured": False,
            "message": "RAILWAY_API_TOKEN not set"
        }
    except Exception as e:
        logger.error(f"Railway health check failed: {e}")
        return {
            "status": "unhealthy",
            "configured": True,
            "error": str(e)
        }
