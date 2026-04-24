"""Tests for GitHub workflow monitor."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.auth.github_workflow_monitor import (
    GitHubWorkflowMonitor,
    WorkflowConclusion,
    WorkflowRun,
    WorkflowStatus,
)


@pytest.fixture
def mock_workflow_data():
    """Sample workflow run data from GitHub API."""
    return {
        "id": 12345,
        "name": "CI",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:05:00Z",
        "html_url": "https://github.com/owner/repo/actions/runs/12345",
        "head_branch": "main",
        "head_sha": "abc123def456",
    }


@pytest.fixture
def monitor():
    """Create a workflow monitor instance."""
    return GitHubWorkflowMonitor(
        token="ghp_test_token", owner="test-owner", repo="test-repo", poll_interval=1
    )


def test_workflow_run_from_api_response(mock_workflow_data):
    """Test WorkflowRun creation from API response."""
    run = WorkflowRun.from_api_response(mock_workflow_data)

    assert run.id == 12345
    assert run.name == "CI"
    assert run.status == WorkflowStatus.COMPLETED
    assert run.conclusion == WorkflowConclusion.SUCCESS
    assert run.head_branch == "main"
    assert run.head_sha == "abc123def456"
    assert isinstance(run.created_at, datetime)


def test_workflow_run_from_api_response_no_conclusion():
    """Test WorkflowRun with no conclusion (in progress)."""
    data = {
        "id": 123,
        "name": "Test",
        "status": "in_progress",
        "conclusion": None,
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:05:00Z",
        "html_url": "https://github.com/test/test/actions/runs/123",
        "head_branch": "dev",
        "head_sha": "xyz789",
    }
    run = WorkflowRun.from_api_response(data)

    assert run.status == WorkflowStatus.IN_PROGRESS
    assert run.conclusion is None


@pytest.mark.asyncio
async def test_monitor_context_manager(monitor):
    """Test monitor can be used as async context manager."""
    async with monitor as m:
        assert m._client is not None
        assert isinstance(m._client, httpx.AsyncClient)

    # Client should be closed after exit
    assert m._client.is_closed


@pytest.mark.asyncio
async def test_get_workflow_runs(monitor, mock_workflow_data):
    """Test fetching workflow runs."""
    mock_response = {"workflow_runs": [mock_workflow_data]}

    with patch.object(httpx.AsyncClient, "get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200, json=lambda: mock_response, raise_for_status=lambda: None
        )

        async with monitor:
            runs = await monitor.get_workflow_runs()

        assert len(runs) == 1
        assert runs[0].id == 12345
        assert runs[0].name == "CI"


@pytest.mark.asyncio
async def test_get_workflow_run(monitor, mock_workflow_data):
    """Test fetching a specific workflow run."""
    with patch.object(httpx.AsyncClient, "get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200, json=lambda: mock_workflow_data, raise_for_status=lambda: None
        )

        async with monitor:
            run = await monitor.get_workflow_run(12345)

        assert run.id == 12345
        assert run.status == WorkflowStatus.COMPLETED


@pytest.mark.asyncio
async def test_watch_workflow_run(monitor):
    """Test watching a workflow run for status changes."""
    responses = [
        {
            "id": 123,
            "name": "CI",
            "status": "queued",
            "conclusion": None,
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z",
            "html_url": "https://github.com/test/test/actions/runs/123",
            "head_branch": "main",
            "head_sha": "abc123",
        },
        {
            "id": 123,
            "name": "CI",
            "status": "in_progress",
            "conclusion": None,
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:01:00Z",
            "html_url": "https://github.com/test/test/actions/runs/123",
            "head_branch": "main",
            "head_sha": "abc123",
        },
        {
            "id": 123,
            "name": "CI",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:05:00Z",
            "html_url": "https://github.com/test/test/actions/runs/123",
            "head_branch": "main",
            "head_sha": "abc123",
        },
    ]

    call_count = 0

    def get_response(*args, **kwargs):
        nonlocal call_count
        response = responses[min(call_count, len(responses) - 1)]
        call_count += 1
        return AsyncMock(status_code=200, json=lambda: response, raise_for_status=lambda: None)

    with patch.object(httpx.AsyncClient, "get", side_effect=get_response):
        async with monitor:
            updates = []
            async for run in monitor.watch_workflow_run(123):
                updates.append(run)

            assert len(updates) == 3
            assert updates[0].status == WorkflowStatus.QUEUED
            assert updates[1].status == WorkflowStatus.IN_PROGRESS
            assert updates[2].status == WorkflowStatus.COMPLETED
            assert updates[2].conclusion == WorkflowConclusion.SUCCESS
