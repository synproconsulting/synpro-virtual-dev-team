"""GitHub Actions workflow monitor with real-time status tracking."""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import httpx


class WorkflowStatus(Enum):
    """GitHub Actions workflow run status."""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WAITING = "waiting"
    REQUESTED = "requested"


class WorkflowConclusion(Enum):
    """GitHub Actions workflow run conclusion."""

    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"
    ACTION_REQUIRED = "action_required"
    NEUTRAL = "neutral"


@dataclass
class WorkflowRun:
    """Represents a GitHub Actions workflow run."""

    id: int
    name: str
    status: WorkflowStatus
    conclusion: Optional[WorkflowConclusion]
    created_at: datetime
    updated_at: datetime
    html_url: str
    head_branch: str
    head_sha: str

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "WorkflowRun":
        """Create WorkflowRun from GitHub API response."""
        return cls(
            id=data["id"],
            name=data["name"],
            status=WorkflowStatus(data["status"]),
            conclusion=WorkflowConclusion(data["conclusion"]) if data.get("conclusion") else None,
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
            html_url=data["html_url"],
            head_branch=data["head_branch"],
            head_sha=data["head_sha"],
        )


class GitHubWorkflowMonitor:
    """Monitor GitHub Actions workflows with real-time status updates."""

    def __init__(self, token: str, owner: str, repo: str, poll_interval: int = 30):
        """
        Initialize the workflow monitor.

        Args:
            token: GitHub personal access token
            owner: Repository owner
            repo: Repository name
            poll_interval: Polling interval in seconds (default: 30)
        """
        self.token = token
        self.owner = owner
        self.repo = repo
        self.poll_interval = poll_interval
        self.base_url = "https://api.github.com"
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "GitHubWorkflowMonitor":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def get_workflow_runs(self, workflow_id: Optional[str] = None) -> list[WorkflowRun]:
        """Fetch workflow runs from GitHub API."""
        if not self._client:
            raise RuntimeError("Monitor must be used as async context manager")

        endpoint = f"/repos/{self.owner}/{self.repo}/actions/runs"
        params = {}
        if workflow_id:
            params["workflow_id"] = workflow_id

        response = await self._client.get(f"{self.base_url}{endpoint}", params=params)
        response.raise_for_status()
        data = response.json()

        return [WorkflowRun.from_api_response(run) for run in data["workflow_runs"]]

    async def get_workflow_run(self, run_id: int) -> WorkflowRun:
        """Fetch a specific workflow run by ID."""
        if not self._client:
            raise RuntimeError("Monitor must be used as async context manager")

        endpoint = f"/repos/{self.owner}/{self.repo}/actions/runs/{run_id}"
        response = await self._client.get(f"{self.base_url}{endpoint}")
        response.raise_for_status()

        return WorkflowRun.from_api_response(response.json())

    async def watch_workflow_run(self, run_id: int) -> AsyncIterator[WorkflowRun]:
        """Watch a workflow run and yield status updates in real-time."""
        previous_status: Optional[WorkflowStatus] = None
        previous_conclusion: Optional[WorkflowConclusion] = None

        while True:
            run = await self.get_workflow_run(run_id)

            if run.status != previous_status or run.conclusion != previous_conclusion:
                yield run
                previous_status = run.status
                previous_conclusion = run.conclusion

            if run.status == WorkflowStatus.COMPLETED:
                break

            await asyncio.sleep(self.poll_interval)


from collections.abc import AsyncIterator
