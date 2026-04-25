"""Service layer for sprint dashboard operations."""

from typing import Optional

from src.auth.dashboard_integrations import CIAdapter, GitHubAdapter, JiraAdapter
from src.auth.sprint_dashboard import SprintDashboard, SprintMetrics


class DashboardService:
    """Service for managing sprint dashboard data and integrations."""

    def __init__(
        self,
        jira_adapter: JiraAdapter,
        github_adapter: GitHubAdapter,
        ci_adapter: CIAdapter,
    ) -> None:
        """Initialize dashboard service with integration adapters.
        
        Args:
            jira_adapter: Jira API adapter
            github_adapter: GitHub API adapter
            ci_adapter: CI system adapter
        """
        self.jira_adapter = jira_adapter
        self.github_adapter = github_adapter
        self.ci_adapter = ci_adapter
        self.dashboard = SprintDashboard()

    def refresh_sprint_data(self, sprint_id: str) -> None:
        """Refresh all sprint data from integrations.
        
        Args:
            sprint_id: The sprint identifier to refresh
        """
        # Fetch and add Jira issues
        issues = self.jira_adapter.fetch_sprint_issues(sprint_id)
        for issue in issues:
            self.dashboard.add_issue(issue)

        # Fetch and add pull requests
        pull_requests = self.github_adapter.fetch_pull_requests()
        for pr in pull_requests:
            self.dashboard.add_pull_request(pr)

    def get_dashboard_metrics(self) -> SprintMetrics:
        """Get current sprint metrics.
        
        Returns:
            Sprint metrics summary
        """
        return self.dashboard.get_metrics()

    def get_issue_status(self, jira_key: str) -> Optional[dict[str, any]]:
        """Get comprehensive status for a Jira issue including PRs and CI.
        
        Args:
            jira_key: The Jira issue key
            
        Returns:
            Dictionary with issue status, linked PRs, and CI status
        """
        if jira_key not in self.dashboard._issues:
            return None

        issue = self.dashboard._issues[jira_key]
        linked_prs = self.dashboard.get_prs_for_issue(jira_key)

        return {
            "issue": issue,
            "pull_requests": linked_prs,
            "has_open_prs": any(pr.status.value == "open" for pr in linked_prs),
            "all_ci_passing": all(
                pr.ci_status and pr.ci_status.value == "success"
                for pr in linked_prs
                if pr.ci_status
            ),
        }

    def get_blockers(self) -> list[dict[str, any]]:
        """Identify potential blockers in the sprint.
        
        Returns:
            List of issues with failed CI or stale PRs
        """
        blockers = []
        
        for issue_key in self.dashboard._issues:
            status = self.get_issue_status(issue_key)
            if not status:
                continue
                
            linked_prs = status["pull_requests"]
            
            # Check for failed CI
            failed_ci = any(
                pr.ci_status and pr.ci_status.value == "failed"
                for pr in linked_prs
            )
            
            if failed_ci or (linked_prs and not status["all_ci_passing"]):
                blockers.append({
                    "issue_key": issue_key,
                    "reason": "Failed CI" if failed_ci else "CI not passing",
                    "pull_requests": linked_prs,
                })
        
        return blockers
