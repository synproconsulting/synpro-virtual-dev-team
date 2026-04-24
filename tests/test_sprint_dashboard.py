"""Tests for sprint dashboard functionality."""

from datetime import datetime
from typing import Any
import pytest

from src.auth.sprint_dashboard import (
    SprintDashboard,
    JiraTicket,
    PullRequest,
    CIBuild,
    IntegrationStatus,
)


class MockProvider:
    """Mock data provider for testing."""

    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data

    def fetch_data(self, **kwargs: Any) -> list[dict[str, Any]]:
        return self.data


@pytest.fixture
def mock_jira_data() -> list[dict[str, Any]]:
    return [
        {"key": "SDT-1", "summary": "Task 1", "status": "Done", "assignee": "John", "story_points": 5},
        {"key": "SDT-2", "summary": "Task 2", "status": "In Progress", "assignee": "Jane", "story_points": 3},
    ]


@pytest.fixture
def mock_pr_data() -> list[dict[str, Any]]:
    return [
        {
            "id": "1",
            "title": "PR 1",
            "author": "dev1",
            "status": "merged",
            "jira_keys": ["SDT-1"],
            "created_at": datetime.now(),
        }
    ]


@pytest.fixture
def mock_ci_data() -> list[dict[str, Any]]:
    return [
        {
            "id": "100",
            "status": IntegrationStatus.SUCCESS,
            "pr_id": "1",
            "branch": "main",
            "started_at": datetime.now(),
        }
    ]


def test_sprint_dashboard_initialization(
    mock_jira_data: list[dict[str, Any]],
    mock_pr_data: list[dict[str, Any]],
    mock_ci_data: list[dict[str, Any]],
) -> None:
    """Test dashboard initialization with providers."""
    dashboard = SprintDashboard(
        jira_provider=MockProvider(mock_jira_data),
        pr_provider=MockProvider(mock_pr_data),
        ci_provider=MockProvider(mock_ci_data),
    )
    assert dashboard.jira_provider is not None
    assert dashboard.pr_provider is not None
    assert dashboard.ci_provider is not None


def test_get_sprint_status(
    mock_jira_data: list[dict[str, Any]],
    mock_pr_data: list[dict[str, Any]],
    mock_ci_data: list[dict[str, Any]],
) -> None:
    """Test fetching sprint status."""
    dashboard = SprintDashboard(
        jira_provider=MockProvider(mock_jira_data),
        pr_provider=MockProvider(mock_pr_data),
        ci_provider=MockProvider(mock_ci_data),
    )
    status = dashboard.get_sprint_status("sprint-1")
    
    assert status.sprint_name == "sprint-1"
    assert len(status.tickets) == 2
    assert len(status.pull_requests) == 1
    assert len(status.ci_builds) == 1
    assert status.completion_percentage == 50.0
    assert status.health_score > 0


def test_calculate_completion() -> None:
    """Test completion calculation."""
    dashboard = SprintDashboard(
        jira_provider=MockProvider([]),
        pr_provider=MockProvider([]),
        ci_provider=MockProvider([]),
    )
    
    tickets = [
        JiraTicket("T-1", "Task 1", "Done", "John", 5),
        JiraTicket("T-2", "Task 2", "In Progress", "Jane", 3),
    ]
    
    completion = dashboard._calculate_completion(tickets)
    assert completion == 50.0


def test_calculate_completion_empty() -> None:
    """Test completion with no tickets."""
    dashboard = SprintDashboard(
        jira_provider=MockProvider([]),
        pr_provider=MockProvider([]),
        ci_provider=MockProvider([]),
    )
    
    completion = dashboard._calculate_completion([])
    assert completion == 0.0
