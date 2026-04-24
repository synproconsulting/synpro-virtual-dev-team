"""CI/CD data provider implementation."""

import os
from datetime import datetime
from typing import Any
import requests

from src.auth.sprint_dashboard import IntegrationStatus


class CIProvider:
    """Provider for fetching CI build data from GitHub Actions."""

    def __init__(self, token: str | None = None, repository: str | None = None) -> None:
        """Initialize CI provider.

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
        """Fetch CI builds for a sprint.

        Args:
            **kwargs: Must include 'sprint_id'

        Returns:
            List of CI build dictionaries
        """
        sprint_id = kwargs.get("sprint_id")
        if not sprint_id or not self.repository:
            return []

        url = f"{self.base_url}/repos/{self.repository}/actions/runs"
        params = {"per_page": 100}

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return self._parse_builds(data.get("workflow_runs", []), sprint_id)
        except requests.RequestException:
            return []

    def _parse_builds(self, runs: list[dict[str, Any]], sprint_id: str) -> list[dict[str, Any]]:
        """Parse GitHub Actions API response into build format."""
        builds = []
        for run in runs:
            head_branch = run.get("head_branch", "")
            
            # Filter builds related to sprint
            if sprint_id.lower() in head_branch.lower():
                builds.append(
                    {
                        "id": str(run.get("id", "")),
                        "status": self._map_status(run.get("conclusion")),
                        "pr_id": self._extract_pr_number(run),
                        "branch": head_branch,
                        "started_at": datetime.fromisoformat(
                            run.get("created_at", "").replace("Z", "+00:00")
                        ),
                    }
                )
        return builds

    def _map_status(self, conclusion: str | None) -> IntegrationStatus:
        """Map GitHub Actions conclusion to IntegrationStatus."""
        if conclusion == "success":
            return IntegrationStatus.SUCCESS
        elif conclusion in ["failure", "cancelled", "timed_out"]:
            return IntegrationStatus.FAILURE
        elif conclusion is None:
            return IntegrationStatus.PENDING
        return IntegrationStatus.UNKNOWN

    def _extract_pr_number(self, run: dict[str, Any]) -> str | None:
        """Extract PR number from workflow run if available."""
        pull_requests = run.get("pull_requests", [])
        if pull_requests:
            return str(pull_requests[0].get("number"))
        return None
