"""Sprint status dashboard integrating Jira, PR, and CI data."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol, Any


class IntegrationStatus(Enum):
    """Status enumeration for integration checks."""
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    UNKNOWN = "unknown"


@dataclass
class JiraTicket:
    """Jira ticket information."""
    key: str
    summary: str
    status: str
    assignee: str | None
    story_points: int | None


@dataclass
class PullRequest:
    """Pull request information."""
    id: str
    title: str
    author: str
    status: str
    jira_keys: list[str]
    created_at: datetime


@dataclass
class CIBuild:
    """CI build information."""
    id: str
    status: IntegrationStatus
    pr_id: str | None
    branch: str
    started_at: datetime


@dataclass
class SprintStatus:
    """Aggregated sprint status data."""
    sprint_name: str
    tickets: list[JiraTicket]
    pull_requests: list[PullRequest]
    ci_builds: list[CIBuild]
    completion_percentage: float
    health_score: float


class DataProvider(Protocol):
    """Protocol for data providers (Jira, GitHub, CI)."""

    def fetch_data(self, **kwargs: Any) -> Any:
        """Fetch data from the integration source."""
        ...


class SprintDashboard:
    """Main dashboard class for sprint status visualization."""

    def __init__(
        self,
        jira_provider: DataProvider,
        pr_provider: DataProvider,
        ci_provider: DataProvider,
    ) -> None:
        """Initialize dashboard with data providers.

        Args:
            jira_provider: Provider for Jira data
            pr_provider: Provider for PR data
            ci_provider: Provider for CI data
        """
        self.jira_provider = jira_provider
        self.pr_provider = pr_provider
        self.ci_provider = ci_provider

    def get_sprint_status(self, sprint_id: str) -> SprintStatus:
        """Fetch and aggregate sprint status from all sources.

        Args:
            sprint_id: Sprint identifier

        Returns:
            SprintStatus object with aggregated data
        """
        tickets = self._fetch_jira_tickets(sprint_id)
        pull_requests = self._fetch_pull_requests(sprint_id)
        ci_builds = self._fetch_ci_builds(sprint_id)

        completion = self._calculate_completion(tickets)
        health = self._calculate_health_score(tickets, pull_requests, ci_builds)

        return SprintStatus(
            sprint_name=sprint_id,
            tickets=tickets,
            pull_requests=pull_requests,
            ci_builds=ci_builds,
            completion_percentage=completion,
            health_score=health,
        )

    def _fetch_jira_tickets(self, sprint_id: str) -> list[JiraTicket]:
        """Fetch Jira tickets for the sprint."""
        data = self.jira_provider.fetch_data(sprint_id=sprint_id)
        return [JiraTicket(**ticket) for ticket in data]

    def _fetch_pull_requests(self, sprint_id: str) -> list[PullRequest]:
        """Fetch pull requests related to the sprint."""
        data = self.pr_provider.fetch_data(sprint_id=sprint_id)
        return [PullRequest(**pr) for pr in data]

    def _fetch_ci_builds(self, sprint_id: str) -> list[CIBuild]:
        """Fetch CI builds for the sprint."""
        data = self.ci_provider.fetch_data(sprint_id=sprint_id)
        return [CIBuild(**build) for build in data]

    def _calculate_completion(self, tickets: list[JiraTicket]) -> float:
        """Calculate sprint completion percentage."""
        if not tickets:
            return 0.0
        completed = sum(1 for t in tickets if t.status.lower() in ["done", "closed"])
        return (completed / len(tickets)) * 100

    def _calculate_health_score(self n        self,
        tickets: list[JiraTicket],
        pull_requests: list[PullRequest],
        ci_builds: list[CIBuild],
    ) -> float:
        """Calculate overall sprint health score (0-100)."""
        if not tickets:
            return 0.0

        # Weight factors
        ticket_weight = 0.4
        pr_weight = 0.3
        ci_weight = 0.3

        # Ticket score: percentage in progress or done
        active_tickets = sum(
            1 for t in tickets if t.status.lower() not in ["to do", "backlog"]
        )
        ticket_score = (active_tickets / len(tickets)) * 100 if tickets else 0

        # PR score: percentage merged or approved
        good_prs = sum(1 for pr in pull_requests if pr.status in ["merged", "approved"])
        pr_score = (good_prs / len(pull_requests)) * 100 if pull_requests else 50

        # CI score: percentage successful builds
        successful_builds = sum(
            1 for b in ci_builds if b.status == IntegrationStatus.SUCCESS
        )
        ci_score = (successful_builds / len(ci_builds)) * 100 if ci_builds else 50

        return (
            ticket_score * ticket_weight + pr_score * pr_weight + ci_score * ci_weight
        )
