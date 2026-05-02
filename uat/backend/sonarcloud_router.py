"""
SonarCloud router - SDT1-61
Provides endpoints for triggering SonarCloud analysis and fetching results.
"""

import os
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
import httpx

logger = logging.getLogger(__name__)

# Configuration
SONARCLOUD_API_BASE = "https://sonarcloud.io/api"
SONARCLOUD_TOKEN = os.getenv("SONARCLOUD_TOKEN", "")
SONARCLOUD_ORG = os.getenv("SONARCLOUD_ORG", "")

router = APIRouter(prefix="/api/sonarcloud", tags=["sonarcloud"])


class SonarTriggerRequest(BaseModel):
    """Request model for triggering SonarCloud analysis."""
    projectKey: str = Field(..., description="SonarCloud project key")
    branch: Optional[str] = Field(default="main", description="Branch to analyze")
    pullRequest: Optional[str] = Field(default=None, description="PR number if analyzing a PR")


class SonarMetric(BaseModel):
    """Individual metric from SonarCloud."""
    name: str
    value: str
    description: Optional[str] = None


class SonarIssuesSummary(BaseModel):
    """Summary of issues by type."""
    bugs: int = 0
    vulnerabilities: int = 0
    codeSmells: int = 0
    securityHotspots: int = 0


class SonarResultsResponse(BaseModel):
    """Response model for SonarCloud results."""
    projectKey: str
    qualityGateStatus: str
    metrics: list[SonarMetric]
    issues: SonarIssuesSummary
    coverage: Optional[str] = None
    duplications: Optional[str] = None
    dashboardUrl: str


def _get_sonar_headers() -> Dict[str, str]:
    """Get headers for SonarCloud API requests."""
    if not SONARCLOUD_TOKEN:
        logger.warning("SONARCLOUD_TOKEN not configured")
        return {"Accept": "application/json"}
    
    return {
        "Authorization": f"Bearer {SONARCLOUD_TOKEN}",
        "Accept": "application/json",
    }


@router.post("/trigger")
async def trigger_sonarcloud_analysis(config: SonarTriggerRequest) -> Dict[str, Any]:
    """
    Trigger a SonarCloud analysis.
    
    Note: This endpoint returns information for triggering an analysis,
    but the actual scan needs to be run via GitHub Actions or CLI.
    For a real implementation, you would integrate with GitHub Actions API
    or use SonarCloud scanner CLI.
    """
    if not config.projectKey:
        raise HTTPException(status_code=400, detail="Project key is required")
    
    # Generate dashboard URL
    dashboard_url = f"https://sonarcloud.io/dashboard?id={config.projectKey}"
    if config.branch and config.branch != "main":
        dashboard_url += f"&branch={config.branch}"
    if config.pullRequest:
        dashboard_url += f"&pullRequest={config.pullRequest}"
    
    logger.info(f"Analysis trigger requested for project {config.projectKey}")
    
    return {
        "success": True,
        "message": "To trigger analysis, run the GitHub Actions workflow or SonarScanner CLI",
        "projectKey": config.projectKey,
        "branch": config.branch,
        "dashboardUrl": dashboard_url,
        "instructions": "Run: gh workflow run sonarcloud.yml"
    }


@router.get("/results")
async def fetch_sonarcloud_results(
    projectKey: str = Query(..., description="SonarCloud project key"),
    branch: Optional[str] = Query(default="main", description="Branch name")
) -> SonarResultsResponse:
    """
    Fetch SonarCloud analysis results for a project.
    
    Retrieves quality gate status, metrics, and issues summary.
    """
    if not projectKey:
        raise HTTPException(status_code=400, detail="Project key is required")
    
    if not SONARCLOUD_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="SonarCloud token not configured. Set SONARCLOUD_TOKEN environment variable."
        )
    
    headers = _get_sonar_headers()
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            # Fetch quality gate status
            qg_params = {"projectKey": projectKey}
            if branch and branch != "main":
                qg_params["branch"] = branch
            
            qg_response = await client.get(
                f"{SONARCLOUD_API_BASE}/qualitygates/project_status",
                headers=headers,
                params=qg_params
            )
            
            if qg_response.status_code != 200:
                logger.error(f"SonarCloud API error: {qg_response.status_code} - {qg_response.text}")
                raise HTTPException(
                    status_code=qg_response.status_code,
                    detail=f"Failed to fetch quality gate status: {qg_response.text}"
                )
            
            qg_data = qg_response.json()
            quality_gate_status = qg_data.get("projectStatus", {}).get("status", "UNKNOWN")
            
            # Fetch component measures (metrics)
            metrics_keys = [
                "bugs", "vulnerabilities", "code_smells", "security_hotspots",
                "coverage", "duplicated_lines_density", "ncloc", "sqale_index"
            ]
            
            measures_params = {
                "component": projectKey,
                "metricKeys": ",".join(metrics_keys)
            }
            if branch and branch != "main":
                measures_params["branch"] = branch
            
            measures_response = await client.get(
                f"{SONARCLOUD_API_BASE}/measures/component",
                headers=headers,
                params=measures_params
            )
            
            if measures_response.status_code != 200:
                logger.error(f"Failed to fetch measures: {measures_response.status_code}")
                # Continue with partial data
                measures_data = {"component": {"measures": []}}
            else:
                measures_data = measures_response.json()
            
            # Parse metrics
            measures = measures_data.get("component", {}).get("measures", [])
            metrics_dict = {m["metric"]: m.get("value", "0") for m in measures}
            
            # Build metrics list for response
            metric_mapping = {
                "bugs": "Bugs",
                "vulnerabilities": "Vulnerabilities",
                "code_smells": "Code Smells",
                "security_hotspots": "Security Hotspots",
                "coverage": "Coverage",
                "duplicated_lines_density": "Duplications",
                "ncloc": "Lines of Code",
                "sqale_index": "Technical Debt"
            }
            
            metrics_list = []
            for key, label in metric_mapping.items():
                value = metrics_dict.get(key, "0")
                if key == "coverage":
                    value = f"{value}%"
                elif key == "duplicated_lines_density":
                    value = f"{value}%"
                elif key == "sqale_index":
                    # Convert minutes to hours/days
                    minutes = int(value) if value.isdigit() else 0
                    if minutes >= 1440:
                        value = f"{minutes / 1440:.1f}d"
                    elif minutes >= 60:
                        value = f"{minutes / 60:.1f}h"
                    else:
                        value = f"{minutes}m"
                
                metrics_list.append(SonarMetric(name=label, value=value))
            
            # Build issues summary
            issues = SonarIssuesSummary(
                bugs=int(metrics_dict.get("bugs", "0")),
                vulnerabilities=int(metrics_dict.get("vulnerabilities", "0")),
                codeSmells=int(metrics_dict.get("code_smells", "0")),
                securityHotspots=int(metrics_dict.get("security_hotspots", "0"))
            )
            
            # Build dashboard URL
            dashboard_url = f"https://sonarcloud.io/dashboard?id={projectKey}"
            if branch and branch != "main":
                dashboard_url += f"&branch={branch}"
            
            return SonarResultsResponse(
                projectKey=projectKey,
                qualityGateStatus=quality_gate_status,
                metrics=metrics_list,
                issues=issues,
                coverage=metrics_dict.get("coverage"),
                duplications=metrics_dict.get("duplicated_lines_density"),
                dashboardUrl=dashboard_url
            )
            
        except httpx.TimeoutException:
            logger.error("SonarCloud API request timed out")
            raise HTTPException(status_code=504, detail="SonarCloud API request timed out")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error communicating with SonarCloud: {e}")
            raise HTTPException(status_code=502, detail=f"Error communicating with SonarCloud: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching SonarCloud results: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/metrics")
async def fetch_sonarcloud_metrics(
    projectKey: str = Query(..., description="SonarCloud project key"),
    metrics: Optional[str] = Query(default=None, description="Comma-separated list of metric keys")
) -> Dict[str, Any]:
    """
    Fetch specific metrics for a SonarCloud project.
    """
    if not projectKey:
        raise HTTPException(status_code=400, detail="Project key is required")
    
    if not SONARCLOUD_TOKEN:
        raise HTTPException(status_code=500, detail="SonarCloud token not configured")
    
    headers = _get_sonar_headers()
    
    # Default metrics if none specified
    if not metrics:
        metrics = "bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density"
    
    params = {
        "component": projectKey,
        "metricKeys": metrics
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(
                f"{SONARCLOUD_API_BASE}/measures/component",
                headers=headers,
                params=params
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"SonarCloud API error: {response.text}"
                )
            
            return response.json()
            
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Request timed out")
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Error: {str(e)}")


@router.get("/quality-gate")
async def fetch_quality_gate_status(
    projectKey: str = Query(..., description="SonarCloud project key"),
    branch: Optional[str] = Query(default="main", description="Branch name")
) -> Dict[str, Any]:
    """
    Fetch quality gate status for a SonarCloud project.
    """
    if not projectKey:
        raise HTTPException(status_code=400, detail="Project key is required")
    
    if not SONARCLOUD_TOKEN:
        raise HTTPException(status_code=500, detail="SonarCloud token not configured")
    
    headers = _get_sonar_headers()
    params = {"projectKey": projectKey}
    
    if branch and branch != "main":
        params["branch"] = branch
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(
                f"{SONARCLOUD_API_BASE}/qualitygates/project_status",
                headers=headers,
                params=params
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"SonarCloud API error: {response.text}"
                )
            
            return response.json()
            
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Request timed out")
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Error: {str(e)}")


@router.get("/projects")
async def list_sonarcloud_projects() -> Dict[str, Any]:
    """
    List all SonarCloud projects in the configured organization.
    """
    if not SONARCLOUD_TOKEN:
        raise HTTPException(status_code=500, detail="SonarCloud token not configured")
    
    if not SONARCLOUD_ORG:
        raise HTTPException(status_code=500, detail="SONARCLOUD_ORG not configured")
    
    headers = _get_sonar_headers()
    params = {"organization": SONARCLOUD_ORG}
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(
                f"{SONARCLOUD_API_BASE}/components/search",
                headers=headers,
                params=params
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"SonarCloud API error: {response.text}"
                )
            
            data = response.json()
            components = data.get("components", [])
            
            # Filter for projects only
            projects = [
                {
                    "key": c["key"],
                    "name": c["name"],
                    "qualifier": c.get("qualifier", ""),
                }
                for c in components
                if c.get("qualifier") == "TRK"
            ]
            
            return {
                "projects": projects,
                "total": len(projects)
            }
            
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Request timed out")
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Error: {str(e)}")
