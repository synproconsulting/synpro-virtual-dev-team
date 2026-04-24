"""Tests for sprint dashboard."""

from datetime import datetime
from unittest.mock import Mock
import pytest
from src.auth.sprint_dashboard import (
    SprintDashboard, JiraTicket, PullRequest, CIBuild, StatusType, SprintMetrics
)


@pytest.fixture
def mock_providers():
    """Create mock data providers."""
    jira_mock = Mock()
    pr_mock = Mock()
    ci_mock = Mock()
    return jira_mock, pr_mock, ci_mock


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    tickets = [
        JiraTicket("SDT-1", "Task 1", "Done", "Alice", 5),
        JiraTicket("SDT-2", "Task 2", "In Progress", "Bob", 3),
    ]
    prs = [
        PullRequest("1", "PR 1", "Alice", StatusType.SUCCESS, ["SDT-1"], "url1"),
        PullRequest("2", "PR 2", "Bob", StatusType.PENDING, ["SDT-2"], "url2"),
    ]
    builds = [
        CIBuild("100", StatusType.SUCCESS, "1", datetime.now()),
        CIBuild("101", StatusType.FAILED, "2", datetime.now()),
    ]
    return tickets, prs, builds


def test_dashboard_initialization(mock_providers):
    """Test dashboard initialization."""
    jira, pr, ci = mock_providers
    dashboard = SprintDashboard(jira, pr, ci)
    assert dashboard is not None


def test_refresh_data(mock_providers, sample_data):
    """Test data refresh."""
    jira, pr, ci = mock_providers
    tickets, prs, builds = sample_data
    
    jira.fetch_data.return_value = tickets
    pr.fetch_data.return_value = prs
    ci.fetch_data.return_value = builds
    
    dashboard = SprintDashboard(jira, pr, ci)
    dashboard.refresh_data("SPRINT-1")
    
    jira.fetch_data.assert_called_once_with(sprint_id="SPRINT-1")
    pr.fetch_data.assert_called_once_with(sprint_id="SPRINT-1")
    ci.fetch_data.assert_called_once_with(sprint_id="SPRINT-1")


def test_get_metrics(mock_providers, sample_data):
    """Test metrics calculation."""
    jira, pr, ci = mock_providers
    tickets, prs, builds = sample_data
    
    jira.fetch_data.return_value = tickets
    pr.fetch_data.return_value = prs
    ci.fetch_data.return_value = builds
    
    dashboard = SprintDashboard(jira, pr, ci)
    dashboard.refresh_data("SPRINT-1")
    metrics = dashboard.get_metrics()
    
    assert metrics.total_tickets == 2
    assert metrics.completed_tickets == 1
    assert metrics.total_story_points == 8
    assert metrics.completed_story_points == 5
    assert metrics.open_prs == 1
    assert metrics.merged_prs == 1
    assert metrics.failed_builds == 1
    assert metrics.success_rate == 0.5


def test_get_ticket_status(mock_providers, sample_data):
    """Test ticket status retrieval."""
    jira, pr, ci = mock_providers
    tickets, prs, builds = sample_data
    
    jira.fetch_data.return_value = tickets
    pr.fetch_data.return_value = prs
    ci.fetch_data.return_value = builds
    
    dashboard = SprintDashboard(jira, pr, ci)
    dashboard.refresh_data("SPRINT-1")
    status = dashboard.get_ticket_status("SDT-1")
    
    assert status["ticket"].key == "SDT-1"
    assert len(status["prs"]) == 1
    assert len(status["builds"]) == 1
    assert status["overall_status"] == StatusType.SUCCESS


def test_overall_status_computation(mock_providers, sample_data):
    """Test overall status computation."""
    jira, pr, ci = mock_providers
    tickets, prs, builds = sample_data
    
    jira.fetch_data.return_value = tickets
    pr.fetch_data.return_value = prs
    ci.fetch_data.return_value = builds
    
    dashboard = SprintDashboard(jira, pr, ci)
    dashboard.refresh_data("SPRINT-1")
    
    # Ticket with failed build
    status = dashboard.get_ticket_status("SDT-2")
    assert status["overall_status"] == StatusType.FAILED
