"""Pull request data provider for sprint dashboard."""

import os
import re
from typing import Any
import requests
from src.auth.sprint_dashboard import PullRequest, StatusType


class PRProvider:
    """Provider for fetching pull request data from GitHub."""
    
    def __init__(self, token: str | None = None, repo: str | None = None) -> None:
        """Initialize PR provider.
        
        Args:
            token: GitHub API token (defaults to GITHUB_TOKEN env var)
            repo: Repository in format 'owner/repo' (defaults to GITHUB_REPO env var)
        """
        self._token = token or os.getenv("GITHUB_TOKEN", "")
        self._repo = repo or os.getenv("GITHUB_REPO", "")
        self._session = requests.Session()
        
        if self._token:
            self._session.headers.update({"Authorization": f"Bearer {self._token}"})
    
    def fetch_data(self, **kwargs: Any) -> list[PullRequest]:
        """Fetch pull requests for a sprint.
        
        Args:
            **kwargs: May include 'sprint_id' for filtering
            
        Returns:
            List of PullRequest objects
            
        Raises:
            requests.RequestException: If API call fails
        """
        sprint_id = kwargs.get("sprint_id", "")
        url = f"https://api.github.com/repos/{self._repo}/pulls"
        params = {"state": "all", "per_page": 100}
        
        response = self._session.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        prs = []
        for pr in data:
            jira_keys = self._extract_jira_keys(pr.get("title", "") + " " + pr.get("body", ""))
            
            # Filter by sprint if provided
            if sprint_id and sprint_id not in pr.get("title", "") and sprint_id not in pr.get("body", ""):
                if not jira_keys:  # Skip if no Jira keys found
                    continue
            
            status = self._map_pr_status(pr)
            prs.append(PullRequest(
                id=str(pr["number"]),
                title=pr["title"],
                author=pr["user"]["login"],
                status=status,
                jira_keys=jira_keys,
                url=pr["html_url"]
            ))
        
        return prs
    
    def _extract_jira_keys(self, text: str) -> list[str]:
        """Extract Jira ticket keys from text."""
        pattern = r"\b([A-Z]{2,10}-\d+)\b"
        return list(set(re.findall(pattern, text)))
    
    def _map_pr_status(self, pr: dict[str, Any]) -> StatusType:
        """Map GitHub PR state to StatusType."""
        if pr.get("merged"):
            return StatusType.SUCCESS
        if pr.get("state") == "closed":
            return StatusType.FAILED
        return StatusType.PENDING
