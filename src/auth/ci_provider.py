"""CI build data provider for sprint dashboard."""

import os
from datetime import datetime
from typing import Any
import requests
from src.auth.sprint_dashboard import CIBuild, StatusType


class CIProvider:
    """Provider for fetching CI build data from GitHub Actions."""
    
    def __init__(self, token: str | None = None, repo: str | None = None) -> None:
        """Initialize CI provider.
        
        Args:
            token: GitHub API token (defaults to GITHUB_TOKEN env var)
            repo: Repository in format 'owner/repo' (defaults to GITHUB_REPO env var)
        """
        self._token = token or os.getenv("GITHUB_TOKEN", "")
        self._repo = repo or os.getenv("GITHUB_REPO", "")
        self._session = requests.Session()
        
        if self._token:
            self._session.headers.update({"Authorization": f"Bearer {self._token}"})
    
    def fetch_data(self, **kwargs: Any) -> list[CIBuild]:
        """Fetch CI builds for a sprint.
        
        Args:
            **kwargs: May include 'sprint_id' for filtering
            
        Returns:
            List of CIBuild objects
            
        Raises:
            requests.RequestException: If API call fails
        """
        url = f"https://api.github.com/repos/{self._repo}/actions/runs"
        params = {"per_page": 100}
        
        response = self._session.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        builds = []
        for run in data.get("workflow_runs", []):
            # Extract PR number from associated pull requests
            pr_id = None
            if run.get("pull_requests"):
                pr_id = str(run["pull_requests"][0]["number"])
            
            builds.append(CIBuild(
                build_id=str(run["id"]),
                status=self._map_ci_status(run["conclusion"], run["status"]),
                pr_id=pr_id,
                started_at=datetime.fromisoformat(run["created_at"].replace("Z", "+00:00")),
                completed_at=datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00")) if run.get("updated_at") else None
            ))
        
        return builds
    
    def _map_ci_status(self, conclusion: str | None, status: str) -> StatusType:
        """Map GitHub Actions status to StatusType."""
        if status != "completed":
            return StatusType.PENDING
        if conclusion == "success":
            return StatusType.SUCCESS
        if conclusion in ("failure", "cancelled", "timed_out"):
            return StatusType.FAILED
        return StatusType.IN_PROGRESS
