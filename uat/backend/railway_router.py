"""
railway_router.py
=================
FastAPI router for Railway deployment operations.
Provides endpoints for managing Railway deployments via GraphQL API.
"""

import os
import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from datetime import datetime

from railway_api import get_railway_client, RailwayClient, RailwayAPIError
from auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/railway", tags=["railway"])


# ── Request/Response Models ───────────────────────────────────────────────────


class DeploymentTriggerRequest(BaseModel):
    """Request to trigger a deployment."""
    service_id: str = Field(..., description="Railway service ID")
    environment_id: str = Field(..., description="Railway environment ID")


class RedeployRequest(BaseModel):
    """Request to trigger a redeployment."""
    service_id: str = Field(..., description="Railway service ID")
    environment_id: str = Field(..., description="Railway environment ID")


class DeploymentStatusResponse(BaseModel):
    """Response containing deployment status."""
    id: str
    status: str
    created_at: str
    updated_at: Optional[str] = None
    static_url: Optional[str] = None
    meta: Optional[Dict] = None


class ServiceInfo(BaseModel):
    """Service information."""
    id: str
    name: str
    icon: Optional[str] = None
    created_at: str


class ProjectInfo(BaseModel):
    """Project information."""
    id: str
    name: str
    description: Optional[str] = None
    created_at: str


class EnvironmentInfo(BaseModel):
    """Environment information."""
    id: str
    name: str
    created_at: str


# ── Helper Functions ──────────────────────────────────────────────────────────


def _format_deployment(deployment: Dict) -> DeploymentStatusResponse:
    """Format deployment data from Railway API to response model."""
    return DeploymentStatusResponse(
        id=deployment.get("id", ""),
        status=deployment.get("status", "UNKNOWN"),
        created_at=deployment.get("createdAt", ""),
        updated_at=deployment.get("updatedAt"),
        static_url=deployment.get("staticUrl"),
        meta=deployment.get("meta")
    )


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("/projects", response_model=List[ProjectInfo])
async def get_projects(current_user: Dict = Depends(get_current_user)):
    """
    Get all Railway projects accessible by the configured API token.
    
    Requires authentication.
    """
    try:
        client = await get_railway_client()
        projects = await client.get_projects()
        
        return [
            ProjectInfo(
                id=p["id"],
                name=p["name"],
                description=p.get("description"),
                created_at=p.get("createdAt", "")
            )
            for p in projects
        ]
    
    except RailwayAPIError as e:
        logger.error(f"Railway API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Railway API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/projects/{project_id}/services", response_model=List[ServiceInfo])
async def get_project_services(
    project_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get all services for a specific Railway project.
    
    Args:
        project_id: Railway project ID
        
    Requires authentication.
    """
    try:
        client = await get_railway_client()
        services = await client.get_project_services(project_id)
        
        return [
            ServiceInfo(
                id=s["id"],
                name=s["name"],
                icon=s.get("icon"),
                created_at=s.get("createdAt", "")
            )
            for s in services
        ]
    
    except RailwayAPIError as e:
        logger.error(f"Railway API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Railway API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/projects/{project_id}/environments", response_model=List[EnvironmentInfo])
async def get_project_environments(
    project_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get all environments for a specific Railway project.
    
    Args:
        project_id: Railway project ID
        
    Requires authentication.
    """
    try:
        client = await get_railway_client()
        environments = await client.get_project_environments(project_id)
        
        return [
            EnvironmentInfo(
                id=e["id"],
                name=e["name"],
                created_at=e.get("createdAt", "")
            )
            for e in environments
        ]
    
    except RailwayAPIError as e:
        logger.error(f"Railway API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Railway API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching environments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/services/{service_id}/deployments", response_model=List[DeploymentStatusResponse])
async def get_service_deployments(
    service_id: str,
    limit: int = 10,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get recent deployments for a specific service.
    
    Args:
        service_id: Railway service ID
        limit: Maximum number of deployments to return (default: 10)
        
    Requires authentication.
    """
    try:
        client = await get_railway_client()
        deployments = await client.get_service_deployments(service_id, limit)
        
        return [_format_deployment(d) for d in deployments]
    
    except RailwayAPIError as e:
        logger.error(f"Railway API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Railway API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching deployments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/deployments/trigger", response_model=DeploymentStatusResponse)
async def trigger_deployment(
    request: DeploymentTriggerRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Trigger a new deployment for a service in a specific environment.
    
    Args:
        request: Deployment trigger request with service_id and environment_id
        
    Requires authentication.
    """
    try:
        client = await get_railway_client()
        deployment = await client.trigger_deployment(
            request.service_id,
            request.environment_id
        )
        
        logger.info(
            f"User {current_user.get('email', 'unknown')} triggered deployment "
            f"{deployment.get('id')} for service {request.service_id}"
        )
        
        return _format_deployment(deployment)
    
    except RailwayAPIError as e:
        logger.error(f"Railway API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Railway API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error triggering deployment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/redeploy", response_model=DeploymentStatusResponse)
async def redeploy_service(
    request: RedeployRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Trigger a redeployment for a service in a specific environment.
    
    This is a convenience endpoint that triggers a new deployment,
    effectively redeploying the service with the current configuration.
    
    Args:
        request: Redeploy request with service_id and environment_id
        
    Requires authentication.
    
    Returns:
        DeploymentStatusResponse: New deployment information
    """
    try:
        client = await get_railway_client()
        deployment = await client.trigger_deployment(
            request.service_id,
            request.environment_id
        )
        
        logger.info(
            f"User {current_user.get('email', 'unknown')} triggered redeploy "
            f"{deployment.get('id')} for service {request.service_id}"
        )
        
        return _format_deployment(deployment)
    
    except RailwayAPIError as e:
        logger.error(f"Railway API error during redeploy: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Railway API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during redeploy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/deployments/{deployment_id}", response_model=DeploymentStatusResponse)
async def get_deployment_status(
    deployment_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get the current status of a specific deployment.
    
    Args:
        deployment_id: Railway deployment ID
        
    Requires authentication.
    """
    try:
        client = await get_railway_client()
        deployment = await client.get_deployment_status(deployment_id)
        
        return _format_deployment(deployment)
    
    except RailwayAPIError as e:
        logger.error(f"Railway API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Railway API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching deployment status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/services/{service_id}/variables")
async def get_service_variables(
    service_id: str,
    environment_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get environment variables for a service in a specific environment.
    
    Args:
        service_id: Railway service ID
        environment_id: Railway environment ID
        
    Requires authentication.
    
    Note: Variable values may be redacted based on Railway's visibility settings.
    """
    try:
        client = await get_railway_client()
        variables = await client.get_service_variables(service_id, environment_id)
        
        return {"variables": variables}
    
    except RailwayAPIError as e:
        logger.error(f"Railway API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Railway API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching service variables: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/health")
async def railway_health():
    """
    Health check endpoint for Railway integration.
    Verifies that Railway API token is configured.
    """
    api_token = os.environ.get("RAILWAY_API_TOKEN")
    
    if not api_token:
        return {
            "status": "unhealthy",
            "message": "RAILWAY_API_TOKEN not configured"
        }
    
    return {
        "status": "healthy",
        "message": "Railway API configured"
    }
