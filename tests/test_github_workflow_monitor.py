"""Tests for GitHub workflow monitor."""

import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientResponseError

from src.auth.github_workflow_monitor import (
    GitHubWorkflowMonitor,
    WorkflowConclusion,
    WorkflowRun,
    WorkflowStatus,
)


@pytest.fixture
def mock_workflow_run_data():
    """Sample workflow run data."""
    return {
        "id": 123456789,
        "name": "CI",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:05:00Z",
        "html_url": "https://github.com/owner/repo/actions/runs/123456789",
        "run_number": 42,
        "head_branch": "main",
    }


@pytest.fixture
def mock_token():
    """Mock GitHub token."""
    return "ghp_test_token_123"


def test_workflow_status_enum():
    """Test workflow status enumeration."""
    assert WorkflowStatus.QUEUED == "queued"
    assert WorkflowStatus.IN_PROGRESS == "in_progress"
    assert WorkflowStatus.COMPLETED == "completed"


def test_workflow_conclusion_enum():
    """Test workflow conclusion enumeration."""
    assert WorkflowConclusion.SUCCESS == "success"
    assert WorkflowConclusion.FAILURE == "failure"
    assert WorkflowConclusion.CANCELLED == "cancelled"


def test_workflow_run_model(mock_workflow_run_data):
    """Test WorkflowRun model validation."""
    run = WorkflowRun(**mock_workflow_run_data)
    assert run.id == 123456789
    assert run.name == "CI"
    assert run.status == WorkflowStatus.COMPLETED
    assert run.conclusion == WorkflowConclusion.SUCCESS
    assert run.run_number == 42


def test_monitor_init_with_token(mock_token):
    """Test monitor initialization with explicit token."""
    monitor = GitHubWorkflowMonitor(token=mock_token)
    assert monitor.token == mock_token
    assert monitor.base_url == "https://api.github.com"


def test_monitor_init_from_env(mock_token, monkeypatch):
    """Test monitor initialization from environment variable."""
    monkeypatch.setenv("GITHUB_TOKEN", mock_token)
    monitor = GitHubWorkflowMonitor()
    assert monitor.token == mock_token


def test_monitor_init_no_token():
    """Test monitor initialization fails without token."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="GitHub token must be provided"):
            GitHubWorkflowMonitor()


@pytest.mark.asyncio
async def test_get_workflow_run(mock_token, mock_workflow_run_data):
    """Test getting a specific workflow run."""
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value=mock_workflow_run_data)
    mock_response.raise_for_status = MagicMock()

    with patch("aiohttp.ClientSession") as mock_session_class:
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.__aexit__ = AsyncMock()
        mock_session_class.return_value = mock_session

        async with GitHubWorkflowMonitor(token=mock_token) as monitor:
            run = await monitor.get_workflow_run("owner", "repo", 123456789)
            assert run.id == 123456789
            assert run.status == WorkflowStatus.COMPLETED


@pytest.mark.asyncio
async def test_list_workflow_runs(mock_token, mock_workflow_run_data):
    """Test listing workflow runs."""
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={"workflow_runs": [mock_workflow_run_data]})
    mock_response.raise_for_status = MagicMock()

    with patch("aiohttp.ClientSession") as mock_session_class:
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.__aexit__ = AsyncMock()
        mock_session_class.return_value = mock_session

        async with GitHubWorkflowMonitor(token=mock_token) as monitor:
            runs = await monitor.list_workflow_runs("owner", "repo")
            assert len(runs) == 1
            assert runs[0].id == 123456789


@pytest.mark.asyncio
async def test_monitor_without_context_manager(mock_token):
    """Test that operations fail outside context manager."""
    monitor = GitHubWorkflowMonitor(token=mock_token)
    with pytest.raises(RuntimeError, match="must be used as async context manager"):
        await monitor.get_workflow_run("owner", "repo", 123)
