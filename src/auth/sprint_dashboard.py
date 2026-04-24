"""Sprint status dashboard integrating Jira, PR, and CI data."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol, Any


class StatusType(Enum):
    """Status types for dashboard items."""
    SUCCESS = "success"
    PENDING = "pending"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"


@dataclass
class JiraTicket:
    """Jira ticket information."""
    key: str
    summary: str
    status: str
    assignee: str | None
    story_points: int | None = None


@dataclass
class PullRequest:
    """Pull request information."""
    id: str
    title: str
    author: str
    status: StatusType
    jira_keys: list[str]
    url: str


@dataclass
class CIBuild:
    """CI build information."""
    build_id: str
    status: StatusType
    pr_id: str | None
    started_at: datetime
    completed_at: datetime | None = None


@dataclass
class SprintMetrics:
    """Aggregated sprint metrics."""
    total_tickets: int
    completed_tickets: int
    total_story_points: int
    completed_story_points: int
    open_prs: int
    merged_prs: int
    failed_builds: int
    success_rate: float


class DataProvider(Protocol):
    """Protocol for data providers (Jira, GitHub, CI)."""
    
    def fetch_data(self, **kwargs: Any) -> list[Any]:
        """Fetch data from the provider."""
        ...


class SprintDashboard:
    """Sprint status dashboard with multi-source integration."""
    
    def __init__(
        self,
        jira_provider: DataProvider,
        pr_provider: DataProvider,
        ci_provider: DataProvider
    ) -> None:
        """Initialize dashboard with data providers.
        
        Args:
            jira_provider: Provider for Jira data
            pr_provider: Provider for PR data
            ci_provider: Provider for CI data
        """
        self._jira = jira_provider
        self._pr = pr_provider
        self._ci = ci_provider
        self._tickets: list[JiraTicket] = []
        self._prs: list[PullRequest] = []
        self._builds: list[CIBuild] = []
    
    def refresh_data(self, sprint_id: str) -> None:
        """Refresh all dashboard data for a sprint.
        
        Args:
            sprint_id: The sprint identifier
        """
        self._tickets = self._jira.fetch_data(sprint_id=sprint_id)
        self._prs = self._pr.fetch_data(sprint_id=sprint_id)
        self._builds = self._ci.fetch_data(sprint_id=sprint_id)
    
    def get_metrics(self) -> SprintMetrics:
        """Calculate sprint metrics from current data.
        
        Returns:
            Aggregated sprint metrics
        """
        completed_tickets = [t for t in self._tickets if t.status.lower() == "done"]
        total_points = sum(t.story_points or 0 for t in self._tickets)
        completed_points = sum(t.story_points or 0 for t in completed_tickets)
        
        open_prs = [p for p in self._prs if p.status == StatusType.PENDING]
        merged_prs = [p for p in self._prs if p.status == StatusType.SUCCESS]
        
        failed_builds = [b for b in self._builds if b.status == StatusType.FAILED]
        total_builds = len(self._builds)
        success_rate = 1.0 - (len(failed_builds) / total_builds) if total_builds > 0 else 0.0
        
        return SprintMetrics(
            total_tickets=len(self._tickets),
            completed_tickets=len(completed_tickets),
            total_story_points=total_points,
            completed_story_points=completed_points,
            open_prs=len(open_prs),
            merged_prs=len(merged_prs),
            failed_builds=len(failed_builds),
            success_rate=success_rate
        )
    
    def get_ticket_status(self, jira_key: str) -> dict[str, Any]:
        """Get comprehensive status for a specific ticket.
        
        Args:
            jira_key: Jira ticket key
            
        Returns:
            Dictionary with ticket, PRs, and CI status
        """
        ticket = next((t for t in self._tickets if t.key == jira_key), None)
        related_prs = [p for p in self._prs if jira_key in p.jira_keys]
        pr_ids = [p.id for p in related_prs]
        related_builds = [b for b in self._builds if b.pr_id in pr_ids]
        
        return {
            "ticket": ticket,
            "prs": related_prs,
            "builds": related_builds,
            "overall_status": self._compute_overall_status(ticket, related_prs, related_builds)
        }
    
    def _compute_overall_status(self, ticket: JiraTicket | None, prs: list[PullRequest], builds: list[CIBuild]) -> StatusType:
        """Compute overall status from components."""
        if not ticket:
            return StatusType.FAILED
        if any(b.status == StatusType.FAILED for b in builds):
            return StatusType.FAILED
        if ticket.status.lower() == "done" and all(p.status == StatusType.SUCCESS for p in prs):
            return StatusType.SUCCESS
        return StatusType.IN_PROGRESS
