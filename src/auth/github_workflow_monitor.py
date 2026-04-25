"""GitHub Actions workflow monitor with real-time status tracking."""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

import httpx


class WorkflowStatus(Enum):
    """GitHub Actions workflow status enumeration."""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WAITING = "waiting"
    REQUESTED = "requested"


class WorkflowConclusion(Enum):
    """GitHub Actions workflow conclusion enumeration."""
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
    run_number: int
    event: str
    head_branch: str


class GitHubWorkflowMonitor:
    """Monitor GitHub Actions workflows with real-time status updates."""

    def __init__(self, token: str, owner: str, repo: str):
        """
        Initialize the GitHub workflow monitor.

        Args:
            token: GitHub API token for authentication
            owner: Repository owner (user or organization)
            repo: Repository name
        """
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = "https://api.github.com"
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    async def get_workflow_runs(
        self,
        workflow_id: Optional[str] = None,
        branch: Optional[str] = None,
        status: Optional[WorkflowStatus] = None
    ) -> list[WorkflowRun]:
        """
        Get workflow runs for the repository.

        Args:
            workflow_id: Optional specific workflow ID or filename
            branch: Optional branch name to filter by
            status: Optional status to filter by

        Returns:
            List of WorkflowRun objects
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/actions/runs"
        params = {}
        if branch:
            params["branch"] = branch
        if status:
            params["status"] = status.value

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._headers, params=params)
            response.raise_for_status()
            data = response.json()

        return [
            self._parse_workflow_run(run)
            for run in data.get("workflow_runs", [])
        ]

    async def get_workflow_run(self, run_id: int) -> WorkflowRun:
        """
        Get a specific workflow run by ID.

        Args:
            run_id: The workflow run ID

        Returns:
            WorkflowRun object
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/actions/runs/{run_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._headers)
            response.raise_for_status()
            data = response.json()

        return self._parse_workflow_run(data)

    async def monitor_workflow(
        self,
        run_id: int,
        interval: int = 10,
        timeout: int = 3600
    ) -> WorkflowRun:
        """
        Monitor a workflow run until completion.

        Args:
            run_id: The workflow run ID to monitor
            interval: Polling interval in seconds
            timeout: Maximum time to monitor in seconds

        Returns:
            Final WorkflowRun object

        Raises:
            TimeoutError: If monitoring exceeds timeout
        """
        start_time = datetime.now()
        while True:
            run = await self.get_workflow_run(run_id)
            if run.status == WorkflowStatus.COMPLETED:
                return run

            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed >= timeout:
                raise TimeoutError(f"Workflow monitoring exceeded {timeout}s timeout")

            await asyncio.sleep(interval)

    def _parse_workflow_run(self, data: dict) -> WorkflowRun:
        """Parse workflow run data from GitHub API response."""
        return WorkflowRun(
            id=data["id"],
            name=data["name"],
            status=WorkflowStatus(data["status"]),
            conclusion=WorkflowConclusion(data["conclusion"]) if data.get("conclusion") else None,
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
            html_url=data["html_url"],
            run_number=data["run_number"],
            event=data["event"],
            head_branch=data["head_branch"] or "unknown"
        )
