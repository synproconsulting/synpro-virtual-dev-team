"""Tests for dashboard service layer."""

from unittest.mock import Mock

import pytest

from src.auth.dashboard_integrations import CIAdapter, GitHubAdapter, JiraAdapter
from src.auth.dashboard_service import DashboardService
from src.auth.sprint_dashboard import (
    CIStatus,
    IssueStatus,
    JiraIssue,
    PRStatus,
    PullRequest,
)


class TestDashboardService:
    """Test cases for DashboardService class."""

    @pytest.fixture
    def mock_adapters(self) -> tuple[Mock, Mock, Mock]:
        """Create mock adapters for testing."""
        jira_adapter = Mock(spec=JiraAdapter)
        github_adapter = Mock(spec=GitHubAdapter)
        ci_adapter = Mock(spec=CIAdapter)
        return jira_adapter, github_adapter, ci_adapter

    def test_initialization(self, mock_adapters: tuple[Mock, Mock, Mock]) -> None:
        """Test service initialization."""
        jira, github, ci = mock_adapters
        service = DashboardService(jira, github, ci)
        assert service.jira_adapter == jira
        assert service.github_adapter == github
        assert service.ci_adapter == ci

    def test_refresh_sprint_data(self, mock_adapters: tuple[Mock, Mock, Mock]) -> None:
        """Test refreshing sprint data from integrations."""
        jira, github, ci = mock_adapters
        
        jira.fetch_sprint_issues.return_value = [
            JiraIssue("SDT-1", "Test", IssueStatus.TODO, None, 3)
        ]
        github.fetch_pull_requests.return_value = [
            PullRequest("1", "PR", PRStatus.OPEN, "dev", "SDT-1", CIStatus.PENDING)
        ]
        
        service = DashboardService(jira, github, ci)
        service.refresh_sprint_data("SPRINT-1")
        
        jira.fetch_sprint_issues.assert_called_once_with("SPRINT-1")
        github.fetch_pull_requests.assert_called_once()
        assert len(service.dashboard._issues) == 1
        assert len(service.dashboard._pull_requests) == 1

    def test_get_dashboard_metrics(self, mock_adapters: tuple[Mock, Mock, Mock]) -> None:
        """Test retrieving dashboard metrics."""
        jira, github, ci = mock_adapters
        service = DashboardService(jira, github, ci)
        
        service.dashboard.add_issue(
            JiraIssue("SDT-1", "Task", IssueStatus.DONE, "user", 5)
        )
        
        metrics = service.get_dashboard_metrics()
        assert metrics.total_issues == 1
        assert metrics.completed_issues == 1

    def test_get_issue_status(self, mock_adapters: tuple[Mock, Mock, Mock]) -> None:
        """Test getting comprehensive issue status."""
        jira, github, ci = mock_adapters
        service = DashboardService(jira, github, ci)
        
        service.dashboard.add_issue(
            JiraIssue("SDT-1", "Task", IssueStatus.IN_PROGRESS, "user", 3)
        )
        service.dashboard.add_pull_request(
            PullRequest("1", "PR", PRStatus.OPEN, "dev", "SDT-1", CIStatus.SUCCESS)
        )
        
        status = service.get_issue_status("SDT-1")
        assert status is not None
        assert status["issue"].key == "SDT-1"
        assert len(status["pull_requests"]) == 1
        assert status["has_open_prs"] is True
        assert status["all_ci_passing"] is True

    def test_get_blockers(self, mock_adapters: tuple[Mock, Mock, Mock]) -> None:
        """Test identifying sprint blockers."""
        jira, github, ci = mock_adapters
        service = DashboardService(jira, github, ci)
        
        service.dashboard.add_issue(
            JiraIssue("SDT-1", "Task", IssueStatus.IN_REVIEW, "user", 5)
        )
        service.dashboard.add_pull_request(
            PullRequest("1", "PR", PRStatus.OPEN, "dev", "SDT-1", CIStatus.FAILED)
        )
        
        blockers = service.get_blockers()
        assert len(blockers) == 1
        assert blockers[0]["issue_key"] == "SDT-1"
        assert "Failed CI" in blockers[0]["reason"]
