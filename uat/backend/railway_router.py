"""
railway_router.py
=================
FastAPI router for Railway deployment operations.
Provides endpoints for managing Railway deployments via GraphQL API.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field
from datetime import datetime
from sqlalchemy.orm import Session

from railway_api import get_railway_client, RailwayClient, RailwayAPIError
from auth import get_current_user
from database import get_db
from models import Product

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


def _product_service_id(product: Product, stage: str) -> Optional[str]:
    """Return the Railway service ID for the given pipeline stage from the product."""
    mapping = {
        "dev": product.railway_dev_service_id,
        "test": product.railway_test_service_id,
        "prod": product.railway_prod_service_id,
    }
    return mapping.get(stage)


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("/projects", response_model=List[ProjectInfo])
async def get_projects(current_user: Dict = Depends(get_current_user)):
    """Get all Railway projects accessible by the configured API token."""
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
    """Get all services for a specific Railway project."""
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
    """Get all environments for a specific Railway project."""
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
    """Get recent deployments for a specific service."""
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
    """Trigger a new deployment for a service in a specific environment."""
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
    """Trigger a redeployment for a service in a specific environment."""
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
    """Get the current status of a specific deployment."""
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
    """Get environment variables for a service in a specific environment."""
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
    """Health check endpoint for Railway integration."""
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


# ── Pipeline (DEV / TEST / PROD) ──────────────────────────────────────────────

_PIPELINE_STAGES = ["dev", "test", "prod"]


def _pipeline_service_name(stage: str) -> Optional[str]:
    """Return the Railway service name for the given pipeline stage from env vars."""
    defaults: Dict[str, str] = {"dev": "synpro-virtual-dev-team"}
    return os.environ.get(f"RAILWAY_{stage.upper()}_SERVICE_NAME", defaults.get(stage))


def _railway_env_name() -> str:
    return os.environ.get("RAILWAY_ENVIRONMENT_NAME", "production")


async def _find_service_and_env(
    client: RailwayClient,
    project_id: str,
    service_name: str,
    env_name: str,
) -> tuple:
    """Resolve service ID and environment ID by name within a project."""
    services = await client.get_project_services(project_id)
    service = next((s for s in services if s["name"].lower() == service_name.lower()), None)
    if not service:
        raise RailwayAPIError(f"Service '{service_name}' not found in Railway project")

    envs = await client.get_project_environments(project_id)
    env = next((e for e in envs if e["name"].lower() == env_name.lower()), None)
    if not env:
        raise RailwayAPIError(f"Railway environment '{env_name}' not found")

    return service["id"], env["id"]


@router.get("/pipeline/status")
async def get_pipeline_status(
    product_id: Optional[str] = Query(None),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return deployment status for DEV, TEST, and PROD pipeline stages.

    When product_id is provided, uses that product's per-environment Railway service IDs.
    Falls back to RAILWAY_*_SERVICE_NAME env vars for stages without a configured service ID.
    """
    product = None
    if product_id:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

    project_id = (
        (product.railway_project_id if product and product.railway_project_id else None)
        or os.environ.get("RAILWAY_PROJECT_ID")
    )
    if not project_id:
        raise HTTPException(status_code=503, detail="RAILWAY_PROJECT_ID not configured")

    env_name = _railway_env_name()
    try:
        client = await get_railway_client()
        services = await client.get_project_services(project_id)
        services_by_name = {s["name"].lower(): s for s in services}

        envs = await client.get_project_environments(project_id)
        env = next((e for e in envs if e["name"].lower() == env_name.lower()), None)
        env_id = env["id"] if env else None

        result: Dict[str, Any] = {}
        for stage in _PIPELINE_STAGES:
            direct_svc_id = _product_service_id(product, stage) if product else None

            if direct_svc_id:
                try:
                    deployments = await client.get_service_deployments(direct_svc_id, limit=1)
                    last = deployments[0] if deployments else None
                    last_deployment = (
                        {
                            "id": last["id"],
                            "status": last["status"],
                            "created_at": last.get("createdAt", ""),
                        }
                        if last
                        else None
                    )
                except Exception:
                    last_deployment = None

                result[stage] = {
                    "configured": True,
                    "service_name": product.name,
                    "service_id": direct_svc_id,
                    "environment_id": env_id,
                    "last_deployment": last_deployment,
                    "error": None,
                }
            else:
                svc_name = _pipeline_service_name(stage)
                if not svc_name:
                    result[stage] = {
                        "configured": False,
                        "service_name": None,
                        "service_id": None,
                        "environment_id": env_id,
                        "last_deployment": None,
                        "error": f"RAILWAY_{stage.upper()}_SERVICE_NAME not configured",
                    }
                    continue

                svc = services_by_name.get(svc_name.lower())
                if not svc:
                    result[stage] = {
                        "configured": True,
                        "service_name": svc_name,
                        "service_id": None,
                        "environment_id": env_id,
                        "last_deployment": None,
                        "error": f"Service '{svc_name}' not found in Railway project",
                    }
                    continue

                try:
                    deployments = await client.get_service_deployments(svc["id"], limit=1)
                    last = deployments[0] if deployments else None
                    last_deployment = (
                        {
                            "id": last["id"],
                            "status": last["status"],
                            "created_at": last.get("createdAt", ""),
                        }
                        if last
                        else None
                    )
                except Exception:
                    last_deployment = None

                result[stage] = {
                    "configured": True,
                    "service_name": svc_name,
                    "service_id": svc["id"],
                    "environment_id": env_id,
                    "last_deployment": last_deployment,
                    "error": None,
                }

        return {"environments": result}

    except RailwayAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/pipeline/{target_stage}/promote")
async def promote_pipeline_stage(
    target_stage: str,
    product_id: Optional[str] = Query(None),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Promote to a pipeline stage by triggering a redeploy of its Railway service.

    Only 'test' and 'prod' are valid promotion targets.
    When product_id is provided, uses that product's Railway service ID for the target stage.
    """
    if target_stage not in ("test", "prod"):
        raise HTTPException(status_code=400, detail="Can only promote to 'test' or 'prod'")

    product = None
    if product_id:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

    project_id = (
        (product.railway_project_id if product and product.railway_project_id else None)
        or os.environ.get("RAILWAY_PROJECT_ID")
    )
    if not project_id:
        raise HTTPException(status_code=503, detail="RAILWAY_PROJECT_ID not configured")

    try:
        client = await get_railway_client()
        direct_svc_id = _product_service_id(product, target_stage) if product else None

        if direct_svc_id:
            envs = await client.get_project_environments(project_id)
            env = next((e for e in envs if e["name"].lower() == _railway_env_name().lower()), None)
            if not env:
                raise RailwayAPIError(f"Railway environment '{_railway_env_name()}' not found")
            svc_id = direct_svc_id
            env_id = env["id"]
            display_name = product.name
        else:
            svc_name = _pipeline_service_name(target_stage)
            if not svc_name:
                raise HTTPException(
                    status_code=503,
                    detail=f"RAILWAY_{target_stage.upper()}_SERVICE_NAME not configured",
                )
            svc_id, env_id = await _find_service_and_env(
                client, project_id, svc_name, _railway_env_name()
            )
            display_name = svc_name

        deployment = await client.trigger_deployment(svc_id, env_id)

        logger.info(
            "User %s promoted to %s: service=%s deployment=%s",
            current_user.get("email", "unknown"),
            target_stage,
            display_name,
            deployment.get("id"),
        )

        return {
            "environment": target_stage,
            "service_name": display_name,
            "deployment": {
                "id": deployment.get("id"),
                "status": deployment.get("status"),
                "created_at": deployment.get("createdAt", ""),
            },
        }

    except RailwayAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/pipeline/{stage}/rollback")
async def rollback_pipeline_stage(
    stage: str,
    product_id: Optional[str] = Query(None),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Roll back a pipeline stage to its previous successful deployment.

    When product_id is provided, uses that product's Railway service ID for the stage.
    """
    if stage not in _PIPELINE_STAGES:
        raise HTTPException(status_code=400, detail=f"Unknown pipeline stage: {stage}")

    product = None
    if product_id:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

    project_id = (
        (product.railway_project_id if product and product.railway_project_id else None)
        or os.environ.get("RAILWAY_PROJECT_ID")
    )
    if not project_id:
        raise HTTPException(status_code=503, detail="RAILWAY_PROJECT_ID not configured")

    try:
        client = await get_railway_client()
        direct_svc_id = _product_service_id(product, stage) if product else None

        if direct_svc_id:
            svc_id = direct_svc_id
            display_name = product.name
        else:
            svc_name = _pipeline_service_name(stage)
            if not svc_name:
                raise HTTPException(
                    status_code=503,
                    detail=f"RAILWAY_{stage.upper()}_SERVICE_NAME not configured",
                )
            svc_id, _ = await _find_service_and_env(
                client, project_id, svc_name, _railway_env_name()
            )
            display_name = svc_name

        deployments = await client.get_service_deployments(svc_id, limit=10)
        successful = [d for d in deployments if d.get("status") in ("SUCCESS", "ACTIVE")]

        if len(successful) < 2:
            raise HTTPException(
                status_code=409,
                detail="No previous successful deployment found to roll back to",
            )

        target = successful[1]
        new_deployment = await client.redeploy_deployment(target["id"])

        logger.info(
            "User %s rolled back %s: service=%s redeploying=%s",
            current_user.get("email", "unknown"),
            stage,
            display_name,
            target["id"],
        )

        return {
            "environment": stage,
            "service_name": display_name,
            "rolled_back_to": target["id"],
            "deployment": {
                "id": new_deployment.get("id"),
                "status": new_deployment.get("status"),
                "created_at": new_deployment.get("createdAt", ""),
            },
        }

    except RailwayAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))
