"""Pull request data provider implementation."""

import os
import re
from datetime import datetime
from typing import Any
import requests


class PRProvider:
    """Provider for fetching pull request data from GitHub."""

    def __init__(self, token: str | None = None, repository: str | None = None) -> None:
        """Initialize PR provider.

        Args:
            token: GitHub API token (from env if not provided)
            repository: Repository in format 'owner/repo' (from env if not provided)
        """
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.repository = repository or os.getenv("GITHUB_REPOSITORY", "")
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})

    def fetch_data(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Fetch pull requests for a sprint.

        Args:
            **kwargs: Must include 'sprint_id'

        Returns:
            List of pull request dictionaries
        """
        sprint_id = kwargs.get("sprint_id")
        if not sprint_id or not self.repository:
            return []

        url = f"{self.base_url}/repos/{self.repository}/pulls"
        params = {"state": "all", "per_page": 100}

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            prs = response.json()
            return self._parse_prs(prs, sprint_id)
        except requests.RequestException:
            return []

    def _parse_prs(self, prs: list[dict[str, Any]], sprint_id: str) -> list[dict[str, Any]]:
        """Parse GitHub API response into PR format."""
        parsed_prs = []
        for pr in prs:
            title = pr.get("title", "")
            body = pr.get("body", "")
            jira_keys = self._extract_jira_keys(f"{title} {body}")
            
            # Filter PRs related to sprint (basic heuristic)
            if sprint_id.lower() in title.lower() or sprint_id.lower() in body.lower():
                parsed_prs.append(
                    {
                        "id": str(pr.get("number", "")),
                        "title": title,
                        "author": pr.get("user", {}).get("login", "unknown"),
                        "status": self._get_pr_status(pr),
                        "jira_keys": jira_keys,
                        "created_at": datetime.fromisoformat(
                            pr.get("created_at", "").replace("Z", "+00:00")
                        ),
                    }
                )
        return parsed_prs

    def _extract_jira_keys(self, text: str) -> list[str]:
        """Extract Jira ticket keys from text."""
        pattern = r"\b[A-Z]{2,}-\d+\b"
        return re.findall(pattern, text)

    def _get_pr_status(self, pr: dict[str, Any]) -> str:
        """Determine PR status."""
        if pr.get("merged_at"):
            return "merged"
        elif pr.get("state") == "closed":
            return "closed"
        elif pr.get("draft"):
            return "draft"
        return "open"
