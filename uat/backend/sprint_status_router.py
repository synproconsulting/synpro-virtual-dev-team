"""
sprint_status_router.py
═══════════════════════
API endpoints for sprint status and metrics display in Control Centre.

Provides comprehensive sprint data including:
- Active sprint information
- Story point velocity and burndown
- Issue breakdown by status
- Team member workload
- Sprint health metrics
"""

import base64
import os
from datetime import datetime
from typing import Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# ── Jira config ───────────────────────────────────────────────────────────────

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT = os.getenv("JIRA_PROJECT_KEY", "SDT1")
JIRA_BOARD_ID = os.getenv("JIRA_BOARD_ID", "34")


def _jira_headers() -> dict:
    """Generate Jira API auth headers."""
    creds = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
    encoded = base64.b64encode(creds.encode()).decode()
    return {
        "Authorization": f"Basic {encoded}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


# ── Response Models ───────────────────────────────────────────────────────────

class IssueBreakdown(BaseModel):
    """Breakdown of issues by status."""
    todo: int = Field(..., description="Number of To Do issues")
    in_progress: int = Field(..., description="Number of In Progress issues")
    done: int = Field(..., description="Number of Done issues")
    total: int = Field(..., description="Total number of issues")


class StoryPointMetrics(BaseModel):
    """Story point metrics for the sprint."""
    total: int = Field(..., description="Total story points in sprint")
    completed: int = Field(..., description="Completed story points")
    in_progress: int = Field(..., description="Story points in progress")
    remaining: int = Field(..., description="Remaining story points")
    completion_percentage: float = Field(..., description="Percentage of story points completed")


class TeamMemberWorkload(BaseModel):
    """Workload for a team member."""
    name: str = Field(..., description="Team member display name")
    assigned_issues: int = Field(..., description="Number of assigned issues")
    assigned_points: int = Field(..., description="Story points assigned")
    completed_issues: int = Field(..., description="Number of completed issues")
    completed_points: int = Field(..., description="Story points completed")


class SprintHealthMetrics(BaseModel):
    """Overall sprint health indicators."""
    days_remaining: Optional[int] = Field(None, description="Days remaining in sprint")
    completion_rate: float = Field(..., description="Overall completion rate (0-100)")
    velocity: float = Field(..., description="Average story points per day")
    at_risk: bool = Field(..., description="Whether sprint is at risk")
    risk_factors: List[str] = Field(default_factory=list, description="List of risk factors")


class SprintInfo(BaseModel):
    """Basic sprint information."""
    id: str = Field(..., description="Sprint ID")
    name: str = Field(..., description="Sprint name")
    state: str = Field(..., description="Sprint state (active, closed, future)")
    start_date: Optional[str] = Field(None, description="Sprint start date")
    end_date: Optional[str] = Field(None, description="Sprint end date")
    goal: Optional[str] = Field(None, description="Sprint goal")


class CurrentSprintStatus(BaseModel):
    """Complete current sprint status."""
    sprint: Optional[SprintInfo] = Field(None, description="Sprint information")
    issue_breakdown: IssueBreakdown = Field(..., description="Issue breakdown by status")
    story_points: StoryPointMetrics = Field(..., description="Story point metrics")
    team_workload: List[TeamMemberWorkload] = Field(default_factory=list, description="Team member workload")
    health_metrics: SprintHealthMetrics = Field(..., description="Sprint health metrics")
    last_updated: str = Field(..., description="Timestamp of last update")


# ── Helper Functions ──────────────────────────────────────────────────────────

async def _get_active_sprint() -> Optional[Dict]:
    """Fetch the active sprint from Jira."""
    if not JIRA_BASE_URL:
        return None

    async with httpx.AsyncClient() as client:
        try:
            # Get active sprint from board
            r = await client.get(
                f"{JIRA_BASE_URL}/rest/agile/1.0/board/{JIRA_BOARD_ID}/sprint",
                headers=_jira_headers(),
                params={"state": "active"},
                timeout=15.0,
            )
            r.raise_for_status()
            data = r.json()
            sprints = data.get("values", [])
            return sprints[0] if sprints else None
        except Exception:
            return None


async def _get_sprint_issues(sprint_id: str) -> List[Dict]:
    """Fetch all issues for a sprint."""
    if not JIRA_BASE_URL:
        return []

    jql = (
        f"project = {JIRA_PROJECT} AND sprint = {sprint_id} "
        f"AND issuetype not in (Epic, Sub-task, Subtask) "
        f"ORDER BY status ASC, customfield_10071 ASC"
    )
    fields = "summary,status,priority,issuetype,assignee,customfield_10016,customfield_10071"

    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                f"{JIRA_BASE_URL}/rest/api/3/search",
                headers=_jira_headers(),
                params={"jql": jql, "maxResults": 200, "fields": fields},
                timeout=15.0,
            )
            r.raise_for_status()
            return r.json().get("issues", [])
        except Exception:
            return []


def _calculate_days_remaining(end_date_str: Optional[str]) -> Optional[int]:
    """Calculate days remaining in sprint."""
    if not end_date_str:
        return None
    try:
        end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
        now = datetime.now(end_date.tzinfo)
        delta = end_date - now
        return max(0, delta.days)
    except Exception:
        return None


def _calculate_sprint_health(
    issue_breakdown: IssueBreakdown,
    story_points: StoryPointMetrics,
    days_remaining: Optional[int],
) -> SprintHealthMetrics:
    """Calculate sprint health metrics and identify risk factors."""
    completion_rate = story_points.completion_percentage
    risk_factors = []
    at_risk = False

    # Calculate velocity (points per day)
    velocity = 0.0
    if days_remaining is not None and days_remaining > 0:
        velocity = story_points.completed / max(1, (14 - days_remaining))  # Assume 2-week sprints

    # Risk factor: Low completion rate with limited time
    if days_remaining is not None and days_remaining <= 3 and completion_rate < 70:
        risk_factors.append("Low completion rate with limited time remaining")
        at_risk = True

    # Risk factor: No progress
    if story_points.completed == 0 and days_remaining is not None and days_remaining < 10:
        risk_factors.append("No completed story points yet")
        at_risk = True

    # Risk factor: Many issues in progress
    if issue_breakdown.in_progress > issue_breakdown.done and issue_breakdown.in_progress > 3:
        risk_factors.append("High number of issues in progress")
        at_risk = True

    # Risk factor: Low velocity
    if velocity > 0 and days_remaining is not None and days_remaining > 0:
        required_velocity = story_points.remaining / days_remaining
        if velocity < required_velocity * 0.7:
            risk_factors.append(f"Current velocity ({velocity:.1f} pts/day) below required ({required_velocity:.1f} pts/day)")
            at_risk = True

    return SprintHealthMetrics(
        days_remaining=days_remaining,
        completion_rate=completion_rate,
        velocity=velocity,
        at_risk=at_risk,
        risk_factors=risk_factors,
    )


# ── Router ────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/sprint-status", tags=["sprint-status"])


@router.get("/current", response_model=CurrentSprintStatus)
async def get_current_sprint_status() -> CurrentSprintStatus:
    """
    Get comprehensive status for the current active sprint.

    Returns detailed metrics including:
    - Issue breakdown by status
    - Story point progress
    - Team member workload
    - Sprint health indicators
    """
    try:
        # Get active sprint
        sprint_data = await _get_active_sprint()

        if not sprint_data:
            # Return empty status if no active sprint
            return CurrentSprintStatus(
                sprint=None,
                issue_breakdown=IssueBreakdown(todo=0, in_progress=0, done=0, total=0),
                story_points=StoryPointMetrics(
                    total=0,
                    completed=0,
                    in_progress=0,
                    remaining=0,
                    completion_percentage=0.0,
                ),
                team_workload=[],
                health_metrics=SprintHealthMetrics(
                    days_remaining=None,
                    completion_rate=0.0,
                    velocity=0.0,
                    at_risk=False,
                    risk_factors=[],
                ),
                last_updated=datetime.utcnow().isoformat(),
            )

        # Parse sprint info
        sprint_info = SprintInfo(
            id=str(sprint_data["id"]),
            name=sprint_data.get("name", "Unknown Sprint"),
            state=sprint_data.get("state", "unknown"),
            start_date=sprint_data.get("startDate"),
            end_date=sprint_data.get("endDate"),
            goal=sprint_data.get("goal"),
        )

        # Get sprint issues
        issues = await _get_sprint_issues(str(sprint_data["id"]))

        # Calculate issue breakdown
        todo_count = 0
        in_progress_count = 0
        done_count = 0

        for issue in issues:
            status = issue["fields"].get("status", {}).get("name", "").lower()
            if "done" in status or "closed" in status:
                done_count += 1
            elif "progress" in status or "review" in status:
                in_progress_count += 1
            else:
                todo_count += 1

        issue_breakdown = IssueBreakdown(
            todo=todo_count,
            in_progress=in_progress_count,
            done=done_count,
            total=len(issues),
        )

        # Calculate story point metrics
        total_points = 0
        completed_points = 0
        in_progress_points = 0

        for issue in issues:
            points = issue["fields"].get("customfield_10016") or 0
            status = issue["fields"].get("status", {}).get("name", "").lower()

            total_points += points
            if "done" in status or "closed" in status:
                completed_points += points
            elif "progress" in status or "review" in status:
                in_progress_points += points

        remaining_points = total_points - completed_points
        completion_pct = (completed_points / total_points * 100) if total_points > 0 else 0.0

        story_points = StoryPointMetrics(
            total=total_points,
            completed=completed_points,
            in_progress=in_progress_points,
            remaining=remaining_points,
            completion_percentage=round(completion_pct, 2),
        )

        # Calculate team workload
        team_workload_map: Dict[str, Dict] = {}

        for issue in issues:
            assignee = issue["fields"].get("assignee")
            if not assignee:
                continue

            name = assignee.get("displayName", "Unassigned")
            points = issue["fields"].get("customfield_10016") or 0
            status = issue["fields"].get("status", {}).get("name", "").lower()
            is_done = "done" in status or "closed" in status

            if name not in team_workload_map:
                team_workload_map[name] = {
                    "name": name,
                    "assigned_issues": 0,
                    "assigned_points": 0,
                    "completed_issues": 0,
                    "completed_points": 0,
                }

            team_workload_map[name]["assigned_issues"] += 1
            team_workload_map[name]["assigned_points"] += points

            if is_done:
                team_workload_map[name]["completed_issues"] += 1
                team_workload_map[name]["completed_points"] += points

        team_workload = [
            TeamMemberWorkload(**workload) for workload in team_workload_map.values()
        ]

        # Calculate health metrics
        days_remaining = _calculate_days_remaining(sprint_data.get("endDate"))
        health_metrics = _calculate_sprint_health(issue_breakdown, story_points, days_remaining)

        return CurrentSprintStatus(
            sprint=sprint_info,
            issue_breakdown=issue_breakdown,
            story_points=story_points,
            team_workload=team_workload,
            health_metrics=health_metrics,
            last_updated=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sprint status: {e}",
        )


@router.get("/health-check")
async def health_check() -> Dict:
    """Quick health check endpoint."""
    return {
        "status": "ok",
        "service": "sprint-status",
        "jira_configured": bool(JIRA_BASE_URL and JIRA_EMAIL and JIRA_API_TOKEN),
    }
