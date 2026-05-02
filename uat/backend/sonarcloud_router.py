"""
sonarcloud_router.py
====================
FastAPI router for SonarCloud integration - trigger analysis and fetch results.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sonarcloud", tags=["sonarcloud"])

# ── Configuration ─────────────────────────────────────────────────────────────────────

SONARCLOUD_TOKEN = os.environ.get("SONARCLOUD_TOKEN", "")
SONARCLOUD_ORG = os.environ.get("SONARCLOUD_ORG", "")
SONARCLOUD_API_URL = "https://sonarcloud.io/api"

# ── Models ────────────────────────────────────────────────────────────────────────────

class TriggerAnalysisRequest(BaseModel):
    """Request to trigger SonarCloud analysis."""
    projectKey: str = Field(..., description="SonarCloud project key")
    branch: str = Field(default="main", description="Branch to analyze")
    pullRequest: Optional[str] = Field(None, description="Optional PR number")


class AnalysisResponse(BaseModel):
    """Response from triggering analysis."""
    status: str
    taskId: Optional[str] = None
    dashboardUrl: Optional[str] = None
    message: str


class MetricValue(BaseModel):
    """Individual metric value."""
    name: str
    value: str
    bestValue: Optional[bool] = None


class IssuesCount(BaseModel):
    """Count of issues by type."""
    bugs: int = 0
    vulnerabilities: int = 0
    codeSmells: int = 0
    securityHotspots: int = 0


class QualityGateCondition(BaseModel):
    """Individual quality gate condition."""
    metric: str
    comparator: str
    errorThreshold: Optional[str] = None
    actualValue: Optional[str] = None
    status: str


class ResultsResponse(BaseModel):
    """Detailed SonarCloud results."""
    projectKey: str
    qualityGateStatus: str
    qualityGateConditions: List[QualityGateCondition] = []
    metrics: List[MetricValue]
    issues: IssuesCount
    coverage: Optional[str] = None
    duplications: Optional[str] = None
    dashboardUrl: str


class DetailedIssue(BaseModel):
    """Detailed issue information."""
    key: str
    rule: str
    severity: str
    component: str
    line: Optional[int] = None
    message: str
    type: str
    status: str
    creationDate: str


# ── Helper Functions ──────────────────────────────────────────────────────────────────

def _get_auth_header() -> Dict[str, str]:
    """Get authentication header for SonarCloud API."""
    if not SONARCLOUD_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="SONARCLOUD_TOKEN environment variable not configured"
        )
    return {"Authorization": f"Bearer {SONARCLOUD_TOKEN}"}


async def _fetch_sonarcloud_api(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch data from SonarCloud API."""
    url = f"{SONARCLOUD_API_URL}/{endpoint}"
    headers = _get_auth_header()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"SonarCloud API error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"SonarCloud API error: {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect to SonarCloud: {str(e)}"
            )


# ── Routes ────────────────────────────────────────────────────────────────────────────

@router.post("/trigger", response_model=AnalysisResponse)
async def trigger_analysis(request: TriggerAnalysisRequest) -> AnalysisResponse:
    """
    Trigger a SonarCloud analysis for a project.
    
    Note: In practice, SonarCloud analysis is typically triggered by CI/CD pipelines.
    This endpoint returns a simulated response for demonstration purposes.
    """
    logger.info(f"Triggering analysis for project: {request.projectKey}, branch: {request.branch}")
    
    # Validate token is configured
    if not SONARCLOUD_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="SONARCLOUD_TOKEN not configured"
        )
    
    # In a real implementation, this would trigger a GitHub Actions workflow
    # or use the SonarCloud Scanner CLI. For now, we return a success message.
    dashboard_url = f"https://sonarcloud.io/dashboard?id={request.projectKey}"
    if request.branch != "main":
        dashboard_url += f"&branch={request.branch}"
    if request.pullRequest:
        dashboard_url += f"&pullRequest={request.pullRequest}"
    
    return AnalysisResponse(
        status="success",
        taskId=None,
        dashboardUrl=dashboard_url,
        message=f"Analysis trigger initiated for {request.projectKey}. Check CI/CD pipeline for progress."
    )


@router.get("/results", response_model=ResultsResponse)
async def get_results(
    projectKey: str = Query(..., description="SonarCloud project key"),
    branch: str = Query("main", description="Branch name")
) -> ResultsResponse:
    """
    Fetch SonarCloud analysis results for a project.
    """
    logger.info(f"Fetching results for project: {projectKey}, branch: {branch}")
    
    # Fetch quality gate status
    qg_params = {"projectKey": projectKey}
    if branch != "main":
        qg_params["branch"] = branch
    
    qg_data = await _fetch_sonarcloud_api("qualitygates/project_status", qg_params)
    
    # Fetch measures
    metric_keys = [
        "bugs", "vulnerabilities", "code_smells", "security_hotspots",
        "coverage", "duplicated_lines_density", "ncloc", "complexity",
        "cognitive_complexity", "sqale_rating", "reliability_rating",
        "security_rating", "sqale_index", "technical_debt"
    ]
    
    measures_params = {
        "component": projectKey,
        "metricKeys": ",".join(metric_keys)
    }
    if branch != "main":
        measures_params["branch"] = branch
    
    measures_data = await _fetch_sonarcloud_api("measures/component", measures_params)
    
    # Parse quality gate status
    project_status = qg_data.get("projectStatus", {})
    qg_status = project_status.get("status", "NONE")
    
    # Parse quality gate conditions
    conditions = []
    for condition in project_status.get("conditions", []):
        conditions.append(QualityGateCondition(
            metric=condition.get("metricKey", ""),
            comparator=condition.get("comparator", ""),
            errorThreshold=condition.get("errorThreshold"),
            actualValue=condition.get("actualValue"),
            status=condition.get("status", "NONE")
        ))
    
    # Parse metrics
    metrics = []
    metric_values = {}
    for measure in measures_data.get("component", {}).get("measures", []):
        metric_key = measure.get("metric")
        value = measure.get("value", "0")
        metric_values[metric_key] = value
        
        # Format metric name
        metric_name = metric_key.replace("_", " ").title()
        metrics.append(MetricValue(
            name=metric_name,
            value=value,
            bestValue=measure.get("bestValue")
        ))
    
    # Build issues count
    issues = IssuesCount(
        bugs=int(metric_values.get("bugs", 0)),
        vulnerabilities=int(metric_values.get("vulnerabilities", 0)),
        codeSmells=int(metric_values.get("code_smells", 0)),
        securityHotspots=int(metric_values.get("security_hotspots", 0))
    )
    
    # Dashboard URL
    dashboard_url = f"https://sonarcloud.io/dashboard?id={projectKey}"
    if branch != "main":
        dashboard_url += f"&branch={branch}"
    
    return ResultsResponse(
        projectKey=projectKey,
        qualityGateStatus=qg_status,
        qualityGateConditions=conditions,
        metrics=metrics,
        issues=issues,
        coverage=metric_values.get("coverage"),
        duplications=metric_values.get("duplicated_lines_density"),
        dashboardUrl=dashboard_url
    )


@router.get("/issues", response_model=List[DetailedIssue])
async def get_issues(
    projectKey: str = Query(..., description="SonarCloud project key"),
    branch: str = Query("main", description="Branch name"),
    types: Optional[str] = Query(None, description="Comma-separated issue types: BUG,VULNERABILITY,CODE_SMELL"),
    severities: Optional[str] = Query(None, description="Comma-separated severities: BLOCKER,CRITICAL,MAJOR,MINOR,INFO"),
    statuses: Optional[str] = Query(None, description="Comma-separated statuses: OPEN,CONFIRMED,REOPENED,RESOLVED,CLOSED"),
    page: int = Query(1, ge=1, description="Page number"),
    pageSize: int = Query(100, ge=1, le=500, description="Page size")
) -> List[DetailedIssue]:
    """
    Fetch detailed issues for a project.
    """
    logger.info(f"Fetching issues for project: {projectKey}, branch: {branch}")
    
    params: Dict[str, Any] = {
        "componentKeys": projectKey,
        "p": page,
        "ps": pageSize,
        "resolved": "false"
    }
    
    if branch != "main":
        params["branch"] = branch
    
    if types:
        params["types"] = types
    
    if severities:
        params["severities"] = severities
    
    if statuses:
        params["statuses"] = statuses
    
    issues_data = await _fetch_sonarcloud_api("issues/search", params)
    
    # Parse issues
    detailed_issues = []
    for issue in issues_data.get("issues", []):
        detailed_issues.append(DetailedIssue(
            key=issue.get("key", ""),
            rule=issue.get("rule", ""),
            severity=issue.get("severity", ""),
            component=issue.get("component", ""),
            line=issue.get("line"),
            message=issue.get("message", ""),
            type=issue.get("type", ""),
            status=issue.get("status", ""),
            creationDate=issue.get("creationDate", "")
        ))
    
    return detailed_issues


@router.get("/metrics")
async def get_metrics(
    projectKey: str = Query(..., description="SonarCloud project key"),
    metricKeys: str = Query(..., description="Comma-separated metric keys"),
    branch: str = Query("main", description="Branch name")
) -> Dict[str, Any]:
    """
    Fetch specific metrics for a project.
    """
    logger.info(f"Fetching metrics for project: {projectKey}, metrics: {metricKeys}")
    
    params = {
        "component": projectKey,
        "metricKeys": metricKeys
    }
    
    if branch != "main":
        params["branch"] = branch
    
    return await _fetch_sonarcloud_api("measures/component", params)


@router.get("/quality-gate")
async def get_quality_gate(
    projectKey: str = Query(..., description="SonarCloud project key"),
    branch: str = Query("main", description="Branch name")
) -> Dict[str, Any]:
    """
    Fetch quality gate status for a project.
    """
    logger.info(f"Fetching quality gate for project: {projectKey}, branch: {branch}")
    
    params = {"projectKey": projectKey}
    if branch != "main":
        params["branch"] = branch
    
    return await _fetch_sonarcloud_api("qualitygates/project_status", params)
