"""Integration adapters for Jira, GitHub, and CI systems."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from src.auth.sprint_dashboard import (
    CIStatus,
    IssueStatus,
    JiraIssue,
    PRStatus,
    PullRequest,
)


class JiraAdapter(ABC):
    """Abstract adapter for Jira API integration."""

    def __init__(self, base_url: str, api_token: str) -> None:
        """Initialize Jira adapter.
        
        Args:
            base_url: Jira instance base URL
            api_token: API authentication token
        """
        self.base_url = base_url
        self.api_token = api_token

    @abstractmethod
    def fetch_sprint_issues(self, sprint_id: str) -> list[JiraIssue]:
        """Fetch all issues for a sprint.
        
        Args:
            sprint_id: The sprint identifier
            
        Returns:
            List of Jira issues
        """
        pass

    def _map_status(self, jira_status: str) -> IssueStatus:
        """Map Jira status string to IssueStatus enum.
        
        Args:
            jira_status: Raw Jira status string
            
        Returns:
            Mapped IssueStatus enum value
        """
        status_map = {
            "To Do": IssueStatus.TODO,
            "In Progress": IssueStatus.IN_PROGRESS,
            "In Review": IssueStatus.IN_REVIEW,
            "Done": IssueStatus.DONE,
        }
        return status_map.get(jira_status, IssueStatus.TODO)


class GitHubAdapter(ABC):
    """Abstract adapter for GitHub API integration."""

    def __init__(self, repo_owner: str, repo_name: str, api_token: str) -> None:
        """Initialize GitHub adapter.
        
        Args:
            repo_owner: Repository owner username
            repo_name: Repository name
            api_token: GitHub API token
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_token = api_token

    @abstractmethod
    def fetch_pull_requests(self, state: str = "all") -> list[PullRequest]:
        """Fetch pull requests from GitHub.
        
        Args:
            state: PR state filter (open, closed, all)
            
        Returns:
            List of pull requests
        """
        pass

    def _extract_jira_key(self, text: str) -> Optional[str]:
        """Extract Jira issue key from PR title or body.
        
        Args:
            text: Text to search for Jira key
            
        Returns:
            Jira key if found, None otherwise
        """
        import re
        match = re.search(r'[A-Z]+-\d+', text)
        return match.group(0) if match else None


class CIAdapter(ABC):
    """Abstract adapter for CI system integration."""

    def __init__(self, api_token: str) -> None:
        """Initialize CI adapter.
        
        Args:
            api_token: CI system API token
        """
        self.api_token = api_token

    @abstractmethod
    def get_pipeline_status(self, commit_sha: str) -> CIStatus:
        """Get CI pipeline status for a commit.
        
        Args:
            commit_sha: Git commit SHA
            
        Returns:
            CI pipeline status
        """
        pass

    def _map_ci_status(self, raw_status: str) -> CIStatus:
        """Map raw CI status to CIStatus enum.
        
        Args:
            raw_status: Raw CI status string
            
        Returns:
            Mapped CIStatus enum value
        """
        status_map = {
            "pending": CIStatus.PENDING,
            "running": CIStatus.RUNNING,
            "success": CIStatus.SUCCESS,
            "failed": CIStatus.FAILED,
            "failure": CIStatus.FAILED,
        }
        return status_map.get(raw_status.lower(), CIStatus.PENDING)
