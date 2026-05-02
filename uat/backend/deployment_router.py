"""
backend/deployment_router.py
════════════════════════════
FastAPI router for UAT deployment management via Railway.
Implements SDT1-58: UAT Deploy tab - wire to Railway GraphQL API
"""

import os
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from railway_client import RailwayClient, RailwayAPIError, get_railway_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/deployments", tags=["deployments"])


# ── Pydantic Models ───────────────────────────────────────────────────────────────────


class ServiceInfo(BaseModel):
    """Railway service information."""
    id: str
    name: str
    icon: Optional[str] = None
    created_at: Optional[str] = Field(None, alias="createdAt")
    updated_at: Optional[str] = Field(None, alias="updatedAt")
    
    class Config:
        populate_by_name = True


class EnvironmentInfo(BaseModel):
    """Railway environment information."""
    id: str
    name: str
    created_at: Optional[str] = Field(None, alias="createdAt")
    
    class Config:
        populate_by_name = True


class DeploymentInfo(BaseModel):
    """Railway deployment information."""
    id: str
    status: str
    static_url: Optional[str] = Field(None, alias="staticUrl")
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(None, alias="updatedAt")
    can_rollback: Optional[bool] = Field(None, alias="canRollback")
    can_redeploy: Optional[bool] = Field(None, alias="canRedeploy")
    environment: Optional[dict] = None
    service: Optional[dict] = None
    
    class Config:
        populate_by_name = True


class DeploymentRequest(BaseModel):
    """Request to trigger a new deployment."""
    service_id: str = Field(..., description="Railway service ID to deploy")
    environment_id: Optional[str] = Field(None, description="Railway environment ID (defaults to UAT)")
    custom_branch: Optional[str] = Field(None, description="Optional custom branch to deploy from")
    notes: Optional[str] = Field(None, description="Deployment notes")


class DeploymentResponse(BaseModel):
    """Response after triggering a deployment."""
    deployment_id: str
    status: str
    service_id: str
    environment_id: str
    triggered_at: str
    static_url: Optional[str] = None
    message: str


class DeploymentStatusResponse(BaseModel):
    """Deployment status information."""
    deployment: DeploymentInfo
    message: str


class ServicesListResponse(BaseModel):
    """List of available services."""
    services: List[ServiceInfo]
    total: int


class EnvironmentsListResponse(BaseModel):
    """List of available environments."""
    environments: List[EnvironmentInfo]
    total: int


class DeploymentsListResponse(BaseModel):
    """List of deployments for a service."""
    deployments: List[DeploymentInfo]
    service_id: str
    total: int


# ── Helper Functions ──────────────────────────────────────────────────────────────────


def get_railway_project_id() -> str:
    """
    Get Railway project ID from environment.
    
    Returns:
        Railway project ID
        
    Raises:
        HTTPException: If RAILWAY_PROJECT_ID is not set
    """
    project_id = os.environ.get("RAILWAY_PROJECT_ID")
    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RAILWAY_PROJECT_ID environment variable is not configured",
        )
    return project_id


def get_uat_environment_id() -> str:
    """
    Get Railway UAT environment ID from environment.
    
    Returns:
        Railway UAT environment ID
        
    Raises:
        HTTPException: If RAILWAY_UAT_ENVIRONMENT_ID is not set
    """
    env_id = os.environ.get("RAILWAY_UAT_ENVIRONMENT_ID")
    if not env_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RAILWAY_UAT_ENVIRONMENT_ID environment variable is not configured",
        )
    return env_id


# ── Routes ────────────────────────────────────────────────────────────────────────────


@router.get("/services", response_model=ServicesListResponse)
async def list_services(
    railway_client: RailwayClient = Depends(get_railway_client)
) -> ServicesListResponse:
    """
    List all available services in the Railway project.
    
    Returns:
        List of services that can be deployed
    """
    try:
        project_id = get_railway_project_id()
        services = await railway_client.list_services(project_id)
        
        service_infos = [
            ServiceInfo(
                id=svc["id"],
                name=svc["name"],
                icon=svc.get("icon"),
                createdAt=svc.get("createdAt"),
                updatedAt=svc.get("updatedAt"),
            )
            for svc in services
        ]
        
        return ServicesListResponse(
            services=service_infos,
            total=len(service_infos),
        )
    
    except RailwayAPIError as e:
        logger.error(f"Railway API error listing services: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch services from Railway: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error listing services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list services",
        )


@router.get("/environments", response_model=EnvironmentsListResponse)
async def list_environments(
    railway_client: RailwayClient = Depends(get_railway_client)
) -> EnvironmentsListResponse:
    """
    List all available environments in the Railway project.
    
    Returns:
        List of environments
    """
    try:
        project_id = get_railway_project_id()
        environments = await railway_client.get_environments(project_id)
        
        env_infos = [
            EnvironmentInfo(
                id=env["id"],
                name=env["name"],
                createdAt=env.get("createdAt"),
            )
            for env in environments
        ]
        
        return EnvironmentsListResponse(
            environments=env_infos,
            total=len(env_infos),
        )
    
    except RailwayAPIError as e:
        logger.error(f"Railway API error listing environments: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch environments from Railway: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error listing environments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list environments",
        )


@router.post("/trigger", response_model=DeploymentResponse)
async def trigger_deployment(
    request: DeploymentRequest,
    railway_client: RailwayClient = Depends(get_railway_client)
) -> DeploymentResponse:
    """
    Trigger a new deployment for a service to UAT environment.
    
    Args:
        request: Deployment configuration
        
    Returns:
        Deployment information and status
    """
    try:
        # Use provided environment_id or default to UAT
        environment_id = request.environment_id or get_uat_environment_id()
        
        # Trigger the deployment
        deployment = await railway_client.trigger_deployment(
            service_id=request.service_id,
            environment_id=environment_id,
            use_custom_branch=bool(request.custom_branch),
            custom_branch=request.custom_branch,
        )
        
        logger.info(
            f"Deployment triggered: {deployment['id']} "
            f"(service: {request.service_id}, environment: {environment_id})"
        )
        
        return DeploymentResponse(
            deployment_id=deployment["id"],
            status=deployment["status"],
            service_id=request.service_id,
            environment_id=environment_id,
            triggered_at=deployment["createdAt"],
            static_url=deployment.get("staticUrl"),
            message=f"Deployment triggered successfully for service {request.service_id}",
        )
    
    except RailwayAPIError as e:
        logger.error(f"Railway API error triggering deployment: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to trigger deployment: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error triggering deployment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger deployment",
        )


@router.get("/{deployment_id}", response_model=DeploymentStatusResponse)
async def get_deployment_status(
    deployment_id: str,
    railway_client: RailwayClient = Depends(get_railway_client)
) -> DeploymentStatusResponse:
    """
    Get the current status of a deployment.
    
    Args:
        deployment_id: Railway deployment ID
        
    Returns:
        Current deployment status
    """
    try:
        deployment = await railway_client.get_deployment_status(deployment_id)
        
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment {deployment_id} not found",
            )
        
        return DeploymentStatusResponse(
            deployment=DeploymentInfo(
                id=deployment["id"],
                status=deployment["status"],
                createdAt=deployment["createdAt"],
                updatedAt=deployment.get("updatedAt"),
                staticUrl=deployment.get("staticUrl"),
                canRollback=deployment.get("canRollback"),
                canRedeploy=deployment.get("canRedeploy"),
                environment=deployment.get("environment"),
                service=deployment.get("service"),
            ),
            message=f"Deployment status: {deployment['status']}",
        )
    
    except RailwayAPIError as e:
        logger.error(f"Railway API error fetching deployment status: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch deployment status: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching deployment status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch deployment status",
        )


@router.get("/service/{service_id}/deployments", response_model=DeploymentsListResponse)
async def get_service_deployments(
    service_id: str,
    limit: int = 10,
    railway_client: RailwayClient = Depends(get_railway_client)
) -> DeploymentsListResponse:
    """
    Get recent deployments for a specific service.
    
    Args:
        service_id: Railway service ID
        limit: Maximum number of deployments to return (default: 10)
        
    Returns:
        List of recent deployments
    """
    try:
        deployments = await railway_client.get_service_deployments(
            service_id=service_id,
            limit=limit,
        )
        
        deployment_infos = [
            DeploymentInfo(
                id=dep["id"],
                status=dep["status"],
                createdAt=dep["createdAt"],
                updatedAt=dep.get("updatedAt"),
                staticUrl=dep.get("staticUrl"),
                canRollback=dep.get("canRollback"),
                canRedeploy=dep.get("canRedeploy"),
                environment=dep.get("environment"),
            )
            for dep in deployments
        ]
        
        return DeploymentsListResponse(
            deployments=deployment_infos,
            service_id=service_id,
            total=len(deployment_infos),
        )
    
    except RailwayAPIError as e:
        logger.error(f"Railway API error fetching service deployments: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch deployments: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching service deployments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch deployments",
        )


@router.get("/{deployment_id}/logs")
async def get_deployment_logs(
    deployment_id: str,
    limit: int = 100,
    railway_client: RailwayClient = Depends(get_railway_client)
):
    """
    Get logs for a specific deployment.
    
    Args:
        deployment_id: Railway deployment ID
        limit: Maximum number of log entries (default: 100)
        
    Returns:
        Deployment logs
    """
    try:
        logs = await railway_client.get_deployment_logs(
            deployment_id=deployment_id,
            limit=limit,
        )
        
        return {
            "deployment_id": deployment_id,
            "logs": logs,
            "total": len(logs),
        }
    
    except RailwayAPIError as e:
        logger.error(f"Railway API error fetching deployment logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch deployment logs: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching deployment logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch deployment logs",
        )
