"""
Tests for the Sprint Status API router.
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create a test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_active_sprint():
    """Mock active sprint data from Jira."""
    now = datetime.utcnow()
    return {
        "id": 42,
        "name": "Sprint 42",
        "state": "active",
        "startDate": (now - timedelta(days=7)).isoformat() + "Z",
        "endDate": (now + timedelta(days=7)).isoformat() + "Z",
        "goal": "Deliver critical features for Q1",
    }


@pytest.fixture
def mock_sprint_issues():
    """Mock sprint issues data from Jira."""
    return [
        {
            "key": "SDT1-1",
            "fields": {
                "summary": "Implement login feature",
                "status": {"name": "Done"},
                "customfield_10016": 5,  # story points
                "assignee": {"displayName": "Alice Developer"},
            }
        },
        {
            "key": "SDT1-2",
            "fields": {
                "summary": "Add user profile",
                "status": {"name": "In Progress"},
                "customfield_10016": 3,
                "assignee": {"displayName": "Bob Engineer"},
            }
        },
        {
            "key": "SDT1-3",
            "fields": {
                "summary": "Setup CI pipeline",
                "status": {"name": "Done"},
                "customfield_10016": 2,
                "assignee": {"displayName": "Alice Developer"},
            }
        },
        {
            "key": "SDT1-4",
            "fields": {
                "summary": "Write documentation",
                "status": {"name": "To Do"},
                "customfield_10016": 1,
                "assignee": {"displayName": "Charlie Writer"},
            }
        },
        {
            "key": "SDT1-5",
            "fields": {
                "summary": "Code review",
                "status": {"name": "In Progress"},
                "customfield_10016": 2,
                "assignee": {"displayName": "Bob Engineer"},
            }
        },
    ]


@pytest.mark.asyncio
async def test_get_current_sprint_status_success(client, mock_active_sprint, mock_sprint_issues):
    """Test getting current sprint status with active sprint."""
    with patch("sprint_status_router._get_active_sprint", new_callable=AsyncMock) as mock_get_sprint, \
         patch("sprint_status_router._get_sprint_issues", new_callable=AsyncMock) as mock_get_issues:
        
        mock_get_sprint.return_value = mock_active_sprint
        mock_get_issues.return_value = mock_sprint_issues
        
        response = client.get("/api/sprint-status/current")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check sprint info
        assert data["sprint"]["id"] == "42"
        assert data["sprint"]["name"] == "Sprint 42"
        assert data["sprint"]["state"] == "active"
        assert data["sprint"]["goal"] == "Deliver critical features for Q1"
        
        # Check issue breakdown
        assert data["issue_breakdown"]["total"] == 5
        assert data["issue_breakdown"]["done"] == 2
        assert data["issue_breakdown"]["in_progress"] == 2
        assert data["issue_breakdown"]["todo"] == 1
        
        # Check story points
        assert data["story_points"]["total"] == 13  # 5+3+2+1+2
        assert data["story_points"]["completed"] == 7  # 5+2
        assert data["story_points"]["in_progress"] == 5  # 3+2
        assert data["story_points"]["remaining"] == 6  # 13-7
        assert data["story_points"]["completion_percentage"] > 50
        
        # Check team workload
        assert len(data["team_workload"]) == 3  # Alice, Bob, Charlie
        
        alice = next((m for m in data["team_workload"] if m["name"] == "Alice Developer"), None)
        assert alice is not None
        assert alice["assigned_issues"] == 2
        assert alice["assigned_points"] == 7  # 5+2
        assert alice["completed_issues"] == 2
        assert alice["completed_points"] == 7
        
        bob = next((m for m in data["team_workload"] if m["name"] == "Bob Engineer"), None)
        assert bob is not None
        assert bob["assigned_issues"] == 2
        assert bob["assigned_points"] == 5  # 3+2
        assert bob["completed_issues"] == 0
        assert bob["completed_points"] == 0
        
        # Check health metrics
        assert "health_metrics" in data
        assert data["health_metrics"]["days_remaining"] == 7
        assert data["health_metrics"]["completion_rate"] > 0
        assert "last_updated" in data


@pytest.mark.asyncio
async def test_get_current_sprint_status_no_active_sprint(client):
    """Test getting sprint status when no sprint is active."""
    with patch("sprint_status_router._get_active_sprint", new_callable=AsyncMock) as mock_get_sprint:
        mock_get_sprint.return_value = None
        
        response = client.get("/api/sprint-status/current")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["sprint"] is None
        assert data["issue_breakdown"]["total"] == 0
        assert data["story_points"]["total"] == 0
        assert len(data["team_workload"]) == 0
        assert data["health_metrics"]["at_risk"] is False


@pytest.mark.asyncio
async def test_get_current_sprint_status_at_risk(client, mock_active_sprint, mock_sprint_issues):
    """Test sprint status shows at-risk when completion is low with little time."""
    # Modify sprint to end soon
    now = datetime.utcnow()
    at_risk_sprint = {
        **mock_active_sprint,
        "startDate": (now - timedelta(days=12)).isoformat() + "Z",
        "endDate": (now + timedelta(days=2)).isoformat() + "Z",  # Only 2 days left
    }
    
    # Only 1 done out of 5 issues
    at_risk_issues = [
        {
            "key": "SDT1-1",
            "fields": {
                "summary": "Task 1",
                "status": {"name": "Done"},
                "customfield_10016": 2,
                "assignee": {"displayName": "Dev A"},
            }
        },
        {
            "key": "SDT1-2",
            "fields": {
                "summary": "Task 2",
                "status": {"name": "To Do"},
                "customfield_10016": 5,
                "assignee": {"displayName": "Dev B"},
            }
        },
        {
            "key": "SDT1-3",
            "fields": {
                "summary": "Task 3",
                "status": {"name": "To Do"},
                "customfield_10016": 3,
                "assignee": {"displayName": "Dev C"},
            }
        },
    ]
    
    with patch("sprint_status_router._get_active_sprint", new_callable=AsyncMock) as mock_get_sprint, \
         patch("sprint_status_router._get_sprint_issues", new_callable=AsyncMock) as mock_get_issues:
        
        mock_get_sprint.return_value = at_risk_sprint
        mock_get_issues.return_value = at_risk_issues
        
        response = client.get("/api/sprint-status/current")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be marked as at risk
        assert data["health_metrics"]["at_risk"] is True
        assert len(data["health_metrics"]["risk_factors"]) > 0
        
        # Check that completion rate is low
        assert data["story_points"]["completion_percentage"] == 20.0  # 2/10


@pytest.mark.asyncio
async def test_get_current_sprint_status_unassigned_issues(client, mock_active_sprint):
    """Test sprint status with unassigned issues."""
    unassigned_issues = [
        {
            "key": "SDT1-1",
            "fields": {
                "summary": "Unassigned task",
                "status": {"name": "To Do"},
                "customfield_10016": 5,
                "assignee": None,  # No assignee
            }
        },
    ]
    
    with patch("sprint_status_router._get_active_sprint", new_callable=AsyncMock) as mock_get_sprint, \
         patch("sprint_status_router._get_sprint_issues", new_callable=AsyncMock) as mock_get_issues:
        
        mock_get_sprint.return_value = mock_active_sprint
        mock_get_issues.return_value = unassigned_issues
        
        response = client.get("/api/sprint-status/current")
        
        assert response.status_code == 200
        data = response.json()
        
        # Unassigned issues should not appear in team workload
        assert len(data["team_workload"]) == 0
        
        # But should still count in totals
        assert data["issue_breakdown"]["total"] == 1
        assert data["story_points"]["total"] == 5


@pytest.mark.asyncio
async def test_get_current_sprint_status_zero_story_points(client, mock_active_sprint):
    """Test sprint status with issues that have no story points."""
    no_points_issues = [
        {
            "key": "SDT1-1",
            "fields": {
                "summary": "No points task",
                "status": {"name": "Done"},
                "customfield_10016": None,  # No story points
                "assignee": {"displayName": "Dev A"},
            }
        },
    ]
    
    with patch("sprint_status_router._get_active_sprint", new_callable=AsyncMock) as mock_get_sprint, \
         patch("sprint_status_router._get_sprint_issues", new_callable=AsyncMock) as mock_get_issues:
        
        mock_get_sprint.return_value = mock_active_sprint
        mock_get_issues.return_value = no_points_issues
        
        response = client.get("/api/sprint-status/current")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should handle zero points gracefully
        assert data["story_points"]["total"] == 0
        assert data["story_points"]["completed"] == 0
        assert data["story_points"]["completion_percentage"] == 0.0


def test_health_check_endpoint(client):
    """Test sprint status health check endpoint."""
    response = client.get("/api/sprint-status/health-check")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert data["service"] == "sprint-status"
    assert "jira_configured" in data


@pytest.mark.asyncio
async def test_get_current_sprint_status_error_handling(client):
    """Test error handling when Jira API fails."""
    with patch("sprint_status_router._get_active_sprint", new_callable=AsyncMock) as mock_get_sprint:
        # Simulate an error
        mock_get_sprint.side_effect = Exception("Jira API error")
        
        response = client.get("/api/sprint-status/current")
        
        assert response.status_code == 500
        assert "Failed to fetch sprint status" in response.json()["detail"]


def test_calculate_days_remaining():
    """Test days remaining calculation."""
    from sprint_status_router import _calculate_days_remaining
    
    # Future date
    future = (datetime.utcnow() + timedelta(days=5)).isoformat() + "Z"
    assert _calculate_days_remaining(future) == 5
    
    # Past date should return 0
    past = (datetime.utcnow() - timedelta(days=5)).isoformat() + "Z"
    assert _calculate_days_remaining(past) == 0
    
    # None should return None
    assert _calculate_days_remaining(None) is None
    
    # Invalid format should return None
    assert _calculate_days_remaining("invalid") is None


def test_calculate_sprint_health():
    """Test sprint health calculation."""
    from sprint_status_router import _calculate_sprint_health, IssueBreakdown, StoryPointMetrics
    
    # Healthy sprint
    breakdown = IssueBreakdown(todo=1, in_progress=1, done=8, total=10)
    points = StoryPointMetrics(
        total=20,
        completed=16,
        in_progress=2,
        remaining=4,
        completion_percentage=80.0
    )
    health = _calculate_sprint_health(breakdown, points, days_remaining=7)
    
    assert health.at_risk is False
    assert health.completion_rate == 80.0
    assert len(health.risk_factors) == 0
    
    # At-risk sprint (low completion with little time)
    breakdown_risk = IssueBreakdown(todo=5, in_progress=2, done=3, total=10)
    points_risk = StoryPointMetrics(
        total=20,
        completed=6,
        in_progress=4,
        remaining=14,
        completion_percentage=30.0
    )
    health_risk = _calculate_sprint_health(breakdown_risk, points_risk, days_remaining=2)
    
    assert health_risk.at_risk is True
    assert len(health_risk.risk_factors) > 0


@pytest.mark.asyncio
async def test_team_workload_aggregation(client, mock_active_sprint):
    """Test that team workload is correctly aggregated per team member."""
    issues_multiple_per_person = [
        {
            "key": "SDT1-1",
            "fields": {
                "summary": "Task 1",
                "status": {"name": "Done"},
                "customfield_10016": 3,
                "assignee": {"displayName": "Alice"},
            }
        },
        {
            "key": "SDT1-2",
            "fields": {
                "summary": "Task 2",
                "status": {"name": "Done"},
                "customfield_10016": 5,
                "assignee": {"displayName": "Alice"},
            }
        },
        {
            "key": "SDT1-3",
            "fields": {
                "summary": "Task 3",
                "status": {"name": "In Progress"},
                "customfield_10016": 2,
                "assignee": {"displayName": "Alice"},
            }
        },
    ]
    
    with patch("sprint_status_router._get_active_sprint", new_callable=AsyncMock) as mock_get_sprint, \
         patch("sprint_status_router._get_sprint_issues", new_callable=AsyncMock) as mock_get_issues:
        
        mock_get_sprint.return_value = mock_active_sprint
        mock_get_issues.return_value = issues_multiple_per_person
        
        response = client.get("/api/sprint-status/current")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have only one team member
        assert len(data["team_workload"]) == 1
        
        alice = data["team_workload"][0]
        assert alice["name"] == "Alice"
        assert alice["assigned_issues"] == 3
        assert alice["assigned_points"] == 10  # 3+5+2
        assert alice["completed_issues"] == 2
        assert alice["completed_points"] == 8  # 3+5
