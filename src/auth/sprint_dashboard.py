"""Sprint status dashboard with Jira, PR, and CI integration."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class IssueStatus(Enum):
    """Jira issue status enumeration."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"


class PRStatus(Enum):
    """Pull request status enumeration."""
    OPEN = "open"
    MERGED = "merged"
    CLOSED = "closed"


class CIStatus(Enum):
    """CI pipeline status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class JiraIssue:
    """Jira issue representation."""
    key: str
    summary: str
    status: IssueStatus
    assignee: Optional[str]
    story_points: Optional[int]


@dataclass
class PullRequest:
    """Pull request representation."""
    id: str
    title: str
    status: PRStatus
    author: str
    jira_key: Optional[str]
    ci_status: Optional[CIStatus]


@dataclass
class SprintMetrics:
    """Sprint metrics summary."""
    total_issues: int
    completed_issues: int
    in_progress_issues: int
    total_story_points: int
    completed_story_points: int
    open_prs: int
    merged_prs: int
    failed_ci_runs: int


class SprintDashboard:
    """Sprint status dashboard aggregating Jira, PR, and CI data."""

    def __init__(self) -> None:
        """Initialize the sprint dashboard."""
        self._issues: dict[str, JiraIssue] = {}
        self._pull_requests: dict[str, PullRequest] = {}

    def add_issue(self, issue: JiraIssue) -> None:
        """Add a Jira issue to the dashboard.
        
        Args:
            issue: The Jira issue to add
        """
        self._issues[issue.key] = issue

    def add_pull_request(self, pr: PullRequest) -> None:
        """Add a pull request to the dashboard.
        
        Args:
            pr: The pull request to add
        """
        self._pull_requests[pr.id] = pr

    def get_metrics(self) -> SprintMetrics:
        """Calculate and return sprint metrics.
        
        Returns:
            SprintMetrics object with aggregated data
        """
        total_issues = len(self._issues)
        completed_issues = sum(
            1 for issue in self._issues.values()
            if issue.status == IssueStatus.DONE
        )
        in_progress_issues = sum(
            1 for issue in self._issues.values()
            if issue.status == IssueStatus.IN_PROGRESS
        )
        total_story_points = sum(
            issue.story_points or 0 for issue in self._issues.values()
        )
        completed_story_points = sum(
            issue.story_points or 0 for issue in self._issues.values()
            if issue.status == IssueStatus.DONE
        )
        open_prs = sum(
            1 for pr in self._pull_requests.values()
            if pr.status == PRStatus.OPEN
        )
        merged_prs = sum(
            1 for pr in self._pull_requests.values()
            if pr.status == PRStatus.MERGED
        )
        failed_ci_runs = sum(
            1 for pr in self._pull_requests.values()
            if pr.ci_status == CIStatus.FAILED
        )

        return SprintMetrics(
            total_issues=total_issues,
            completed_issues=completed_issues,
            in_progress_issues=in_progress_issues,
            total_story_points=total_story_points,
            completed_story_points=completed_story_points,
            open_prs=open_prs,
            merged_prs=merged_prs,
            failed_ci_runs=failed_ci_runs,
        )

    def get_prs_for_issue(self, jira_key: str) -> list[PullRequest]:
        """Get all pull requests linked to a Jira issue.
        
        Args:
            jira_key: The Jira issue key
            
        Returns:
            List of pull requests linked to the issue
        """
        return [
            pr for pr in self._pull_requests.values()
            if pr.jira_key == jira_key
        ]
