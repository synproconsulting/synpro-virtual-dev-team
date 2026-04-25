"""Tests for sprint dashboard functionality."""

import pytest

from src.auth.sprint_dashboard import (
    CIStatus,
    IssueStatus,
    JiraIssue,
    PRStatus,
    PullRequest,
    SprintDashboard,
)


class TestSprintDashboard:
    """Test cases for SprintDashboard class."""

    def test_add_issue(self) -> None:
        """Test adding a Jira issue to dashboard."""
        dashboard = SprintDashboard()
        issue = JiraIssue(
            key="SDT-1",
            summary="Test issue",
            status=IssueStatus.TODO,
            assignee="user@example.com",
            story_points=5,
        )
        dashboard.add_issue(issue)
        assert "SDT-1" in dashboard._issues

    def test_add_pull_request(self) -> None:
        """Test adding a pull request to dashboard."""
        dashboard = SprintDashboard()
        pr = PullRequest(
            id="123",
            title="Fix bug",
            status=PRStatus.OPEN,
            author="developer",
            jira_key="SDT-1",
            ci_status=CIStatus.SUCCESS,
        )
        dashboard.add_pull_request(pr)
        assert "123" in dashboard._pull_requests

    def test_get_metrics_empty(self) -> None:
        """Test metrics calculation with no data."""
        dashboard = SprintDashboard()
        metrics = dashboard.get_metrics()
        assert metrics.total_issues == 0
        assert metrics.completed_issues == 0
        assert metrics.open_prs == 0

    def test_get_metrics_with_data(self) -> None:
        """Test metrics calculation with sample data."""
        dashboard = SprintDashboard()
        
        dashboard.add_issue(JiraIssue("SDT-1", "Task 1", IssueStatus.DONE, "user1", 5))
        dashboard.add_issue(JiraIssue("SDT-2", "Task 2", IssueStatus.IN_PROGRESS, "user2", 3))
        dashboard.add_pull_request(PullRequest("1", "PR 1", PRStatus.OPEN, "dev1", "SDT-1", CIStatus.SUCCESS))
        dashboard.add_pull_request(PullRequest("2", "PR 2", PRStatus.MERGED, "dev2", "SDT-2", CIStatus.FAILED))
        
        metrics = dashboard.get_metrics()
        assert metrics.total_issues == 2
        assert metrics.completed_issues == 1
        assert metrics.in_progress_issues == 1
        assert metrics.total_story_points == 8
        assert metrics.completed_story_points == 5
        assert metrics.open_prs == 1
        assert metrics.merged_prs == 1
        assert metrics.failed_ci_runs == 1

    def test_get_prs_for_issue(self) -> None:
        """Test retrieving PRs linked to a specific issue."""
        dashboard = SprintDashboard()
        
        dashboard.add_pull_request(PullRequest("1", "PR 1", PRStatus.OPEN, "dev", "SDT-1", None))
        dashboard.add_pull_request(PullRequest("2", "PR 2", PRStatus.OPEN, "dev", "SDT-2", None))
        dashboard.add_pull_request(PullRequest("3", "PR 3", PRStatus.MERGED, "dev", "SDT-1", None))
        
        prs = dashboard.get_prs_for_issue("SDT-1")
        assert len(prs) == 2
        assert all(pr.jira_key == "SDT-1" for pr in prs)
