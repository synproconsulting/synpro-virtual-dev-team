"""
Deployment router for UAT environment.
Handles Railway deployment operations via GraphQL API.
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from railway_client import RailwayClient, RailwayClientError
from auth import get_current_user

logger = logging.getLogger(__name__)


# ── Request/Response Models ───────────────────────────────────────────────────────────


class ServiceInfo(BaseModel):
    """Railway service information."""
    id: str
    name: str
    icon: Optional[str] = None


class EnvironmentInfo(BaseModel):
    """Railway environment information."""
    id: str
    name: str


class DeploymentTriggerRequest(BaseModel):
    """Request to trigger a deployment."""
    service_ids: List[str] = Field(..., description="List of service IDs to deploy")
    environment_id: Optional[str] = Field(None, description="Environment ID (optional, uses default UAT)")
    deployment_notes: Optional[str] = Field(None, description="Optional notes about this deployment")


class DeploymentStatusResponse(BaseModel):
    """Deployment status information."""
    id: str
    status: str
    service_name: str
    environment_name: str
    created_at: str
    url: Optional[str] = None


class DeploymentTriggerResponse(BaseModel):
    """Response after triggering deployment(s)."""
    success: bool
    message: str
    deployments: List[DeploymentStatusResponse]
    failed_services: List[dict] = []


class DeploymentHistoryResponse(BaseModel):
    """Deployment history."""
    deployments: List[DeploymentStatusResponse]
    total: int


# ── Dependency ────────────────────────────────────────────────────────────────────────


def get_railway_client() -> RailwayClient:
    """
    Get Railway client instance.
    
    Returns:
        Configured RailwayClient instance
        
    Raises:
        HTTPException: If Railway client cannot be initialized
    """
    try:
        return RailwayClient()
    except RailwayClientError as e:
        logger.error(f"Failed to initialize Railway client: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Railway API configuration error: {str(e)}"
        )


# ── Router ────────────────────────────────────────────────────────────────────────────


router = APIRouter(prefix="/api/deployments", tags=["deployments"])


@router.get("/services", response_model=List[ServiceInfo])
async def list_services(
    railway_client: RailwayClient = Depends(get_railway_client),
    current_user: dict = Depends(get_current_user),
):
    """
    List all available services in the Railway project.
    
    Returns:
        List of services with their IDs and names
    """
    try:
        services = await railway_client.list_services()
        return [
            ServiceInfo(
                id=service.id,
                name=service.name,
                icon=service.icon,
            )
            for service in services
        ]
    except RailwayClientError as e:
        logger.error(f"Failed to list services: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/environments", response_model=List[EnvironmentInfo])
async def list_environments(
    railway_client: RailwayClient = Depends(get_railway_client),
    current_user: dict = Depends(get_current_user),
):
    """
    List all available environments in the Railway project.
    
    Returns:
        List of environments with their IDs and names
    """
    try:
        environments = await railway_client.list_environments()
        return [
            EnvironmentInfo(
                id=env.id,
                name=env.name,
            )
            for env in environments
        ]
    except RailwayClientError as e:
        logger.error(f"Failed to list environments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger", response_model=DeploymentTriggerResponse)
async def trigger_deployment(
    request: DeploymentTriggerRequest,
    railway_client: RailwayClient = Depends(get_railway_client),
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger deployment for one or more services.
    
    Args:
        request: Deployment trigger request with service IDs
        
    Returns:
        Deployment trigger response with deployment IDs and statuses
    """
    if not request.service_ids:
        raise HTTPException(
            status_code=400,
            detail="At least one service ID must be provided"
        )
    
    deployments = []
    failed_services = []
    
    for service_id in request.service_ids:
        try:
            logger.info(
                f"User {current_user.get('email', 'unknown')} triggering deployment "
                f"for service {service_id}"
            )
            
            deployment_id = await railway_client.trigger_deployment(
                service_id=service_id,
                environment_id=request.environment_id,
            )
            
            # Get deployment status
            deployment = await railway_client.get_deployment_status(deployment_id)
            
            deployments.append(
                DeploymentStatusResponse(
                    id=deployment.id,
                    status=deployment.status,
                    service_name=deployment.service_name,
                    environment_name=deployment.environment_name,
                    created_at=deployment.created_at,
                    url=deployment.url,
                )
            )
            
        except RailwayClientError as e:
            logger.error(f"Failed to trigger deployment for service {service_id}: {e}")
            failed_services.append({
                "service_id": service_id,
                "error": str(e),
            })
    
    if not deployments and failed_services:
        raise HTTPException(
            status_code=500,
            detail=f"All deployments failed: {failed_services}"
        )
    
    success = len(failed_services) == 0
    message = (
        f"Successfully triggered {len(deployments)} deployment(s)"
        if success
        else f"Triggered {len(deployments)} deployment(s) with {len(failed_services)} failure(s)"
    )
    
    return DeploymentTriggerResponse(
        success=success,
        message=message,
        deployments=deployments,
        failed_services=failed_services,
    )


@router.get("/status/{deployment_id}", response_model=DeploymentStatusResponse)
async def get_deployment_status(
    deployment_id: str,
    railway_client: RailwayClient = Depends(get_railway_client),
    current_user: dict = Depends(get_current_user),
):
    """
    Get the status of a specific deployment.
    
    Args:
        deployment_id: Railway deployment ID
        
    Returns:
        Deployment status information
    """
    try:
        deployment = await railway_client.get_deployment_status(deployment_id)
        return DeploymentStatusResponse(
            id=deployment.id,
            status=deployment.status,
            service_name=deployment.service_name,
            environment_name=deployment.environment_name,
            created_at=deployment.created_at,
            url=deployment.url,
        )
    except RailwayClientError as e:
        logger.error(f"Failed to get deployment status: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/history", response_model=DeploymentHistoryResponse)
async def get_deployment_history(
    service_id: Optional[str] = None,
    limit: int = 10,
    railway_client: RailwayClient = Depends(get_railway_client),
    current_user: dict = Depends(get_current_user),
):
    """
    Get deployment history.
    
    Args:
        service_id: Filter by service ID (optional)
        limit: Maximum number of deployments to return
        
    Returns:
        List of recent deployments
    """
    try:
        deployments = await railway_client.list_deployments(
            service_id=service_id,
            limit=limit,
        )
        
        return DeploymentHistoryResponse(
            deployments=[
                DeploymentStatusResponse(
                    id=d.id,
                    status=d.status,
                    service_name=d.service_name,
                    environment_name=d.environment_name,
                    created_at=d.created_at,
                    url=d.url,
                )
                for d in deployments
            ],
            total=len(deployments),
        )
    except RailwayClientError as e:
        logger.error(f"Failed to get deployment history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/{deployment_id}")
async def get_deployment_logs(
    deployment_id: str,
    limit: int = 100,
    railway_client: RailwayClient = Depends(get_railway_client),
    current_user: dict = Depends(get_current_user),
):
    """
    Get logs for a deployment.
    
    Args:
        deployment_id: Railway deployment ID
        limit: Maximum number of log lines to return
        
    Returns:
        Deployment logs
    """
    try:
        logs = await railway_client.get_service_logs(
            deployment_id=deployment_id,
            limit=limit,
        )
        
        return {
            "deployment_id": deployment_id,
            "logs": logs,
            "total": len(logs),
        }
    except RailwayClientError as e:
        logger.error(f"Failed to get deployment logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
