"""GitHub Actions workflow monitor with real-time status tracking."""

import asyncio
import os
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import aiohttp
from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """GitHub Actions workflow status enumeration."""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WAITING = "waiting"
    REQUESTED = "requested"


class WorkflowConclusion(str, Enum):
    """GitHub Actions workflow conclusion enumeration."""

    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"
    ACTION_REQUIRED = "action_required"
    NEUTRAL = "neutral"


class WorkflowRun(BaseModel):
    """Model representing a GitHub Actions workflow run."""

    id: int
    name: str
    status: WorkflowStatus
    conclusion: Optional[WorkflowConclusion] = None
    created_at: datetime
    updated_at: datetime
    html_url: str
    run_number: int
    head_branch: Optional[str] = None


class GitHubWorkflowMonitor:
    """Monitor GitHub Actions workflows with real-time status updates."""

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        """Initialize the GitHub workflow monitor.

        Args:
            token: GitHub personal access token (defaults to GITHUB_TOKEN env var)
            base_url: GitHub API base URL
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHub token must be provided or set in GITHUB_TOKEN env var")
        self.base_url = base_url
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "GitHubWorkflowMonitor":
        """Async context manager entry."""
        self._session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._session:
            await self._session.close()

    async def get_workflow_run(self, owner: str, repo: str, run_id: int) -> WorkflowRun:
        """Get a specific workflow run by ID.

        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID

        Returns:
            WorkflowRun object with current status
        """
        if not self._session:
            raise RuntimeError("Monitor must be used as async context manager")

        url = f"{self.base_url}/repos/{owner}/{repo}/actions/runs/{run_id}"
        async with self._session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            return WorkflowRun(**data)

    async def list_workflow_runs(
        self, owner: str, repo: str, workflow_id: Optional[str] = None, limit: int = 10
    ) -> list[WorkflowRun]:
        """List workflow runs for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            workflow_id: Optional workflow file name or ID to filter by
            limit: Maximum number of runs to return

        Returns:
            List of WorkflowRun objects
        """
        if not self._session:
            raise RuntimeError("Monitor must be used as async context manager")

        if workflow_id:
            url = f"{self.base_url}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
        else:
            url = f"{self.base_url}/repos/{owner}/{repo}/actions/runs"

        params = {"per_page": limit}
        async with self._session.get(url, params=params) as response:
            response.raise_for_status()
            data = await response.json()
            return [WorkflowRun(**run) for run in data["workflow_runs"]]

    async def watch_workflow_run(
        self, owner: str, repo: str, run_id: int, poll_interval: int = 10
    ) -> AsyncIterator[WorkflowRun]:
        """Watch a workflow run and yield status updates in real-time.

        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID
            poll_interval: Seconds between status checks

        Yields:
            WorkflowRun objects with updated status
        """
        previous_status = None
        previous_conclusion = None

        while True:
            run = await self.get_workflow_run(owner, repo, run_id)

            if run.status != previous_status or run.conclusion != previous_conclusion:
                yield run
                previous_status = run.status
                previous_conclusion = run.conclusion

            if run.status == WorkflowStatus.COMPLETED:
                break

            await asyncio.sleep(poll_interval)
