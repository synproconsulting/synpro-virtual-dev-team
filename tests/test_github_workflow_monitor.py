"""Tests for GitHub workflow monitor."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from src.auth.github_workflow_monitor import (
    GitHubWorkflowMonitor,
    WorkflowConclusion,
    WorkflowRun,
    WorkflowStatus,
)


@pytest.fixture
def monitor():
    """Create a workflow monitor instance."""
    return GitHubWorkflowMonitor(
        token="ghp_test_token",
        owner="test-owner",
        repo="test-repo"
    )


@pytest.fixture
def mock_workflow_data():
    """Mock workflow run data from GitHub API."""
    return {
        "id": 123456,
        "name": "CI Pipeline",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:05:00Z",
        "html_url": "https://github.com/test-owner/test-repo/actions/runs/123456",
        "run_number": 42,
        "event": "push",
        "head_branch": "main"
    }


class TestGitHubWorkflowMonitor:
    """Test suite for GitHubWorkflowMonitor."""

    def test_initialization(self, monitor):
        """Test monitor initialization."""
        assert monitor.token == "ghp_test_token"
        assert monitor.owner == "test-owner"
        assert monitor.repo == "test-repo"
        assert "Bearer ghp_test_token" in monitor._headers["Authorization"]

    @pytest.mark.asyncio
    async def test_get_workflow_runs(self, monitor, mock_workflow_data):
        """Test fetching workflow runs."""
        mock_response = Mock()
        mock_response.json.return_value = {"workflow_runs": [mock_workflow_data]}
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            runs = await monitor.get_workflow_runs()

        assert len(runs) == 1
        assert runs[0].id == 123456
        assert runs[0].name == "CI Pipeline"
        assert runs[0].status == WorkflowStatus.COMPLETED
        assert runs[0].conclusion == WorkflowConclusion.SUCCESS

    @pytest.mark.asyncio
    async def test_get_workflow_run(self, monitor, mock_workflow_data):
        """Test fetching a specific workflow run."""
        mock_response = Mock()
        mock_response.json.return_value = mock_workflow_data
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            run = await monitor.get_workflow_run(123456)

        assert run.id == 123456
        assert run.run_number == 42
        assert run.event == "push"

    @pytest.mark.asyncio
    async def test_monitor_workflow_completes(self, monitor, mock_workflow_data):
        """Test monitoring a workflow until completion."""
        mock_response = Mock()
        mock_response.json.return_value = mock_workflow_data
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            run = await monitor.monitor_workflow(123456, interval=0.1)

        assert run.status == WorkflowStatus.COMPLETED
        assert run.conclusion == WorkflowConclusion.SUCCESS

    @pytest.mark.asyncio
    async def test_monitor_workflow_timeout(self, monitor):
        """Test workflow monitoring timeout."""
        in_progress_data = {
            "id": 123456,
            "name": "CI Pipeline",
            "status": "in_progress",
            "conclusion": None,
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:05:00Z",
            "html_url": "https://github.com/test/repo/actions/runs/123456",
            "run_number": 42,
            "event": "push",
            "head_branch": "main"
        }

        mock_response = Mock()
        mock_response.json.return_value = in_progress_data
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            with pytest.raises(TimeoutError):
                await monitor.monitor_workflow(123456, interval=0.1, timeout=0.5)

    def test_parse_workflow_run(self, monitor, mock_workflow_data):
        """Test parsing workflow run data."""
        run = monitor._parse_workflow_run(mock_workflow_data)

        assert isinstance(run, WorkflowRun)
        assert run.id == 123456
        assert run.status == WorkflowStatus.COMPLETED
        assert run.conclusion == WorkflowConclusion.SUCCESS
        assert isinstance(run.created_at, datetime)
        assert run.head_branch == "main"
