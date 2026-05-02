"""
tests/test_github_ci_wait.py
─────────────────────────────
Unit tests for GitHub CI wait functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from tools.github_ci_wait import (
    get_latest_workflow_run,
    get_workflow_run_status,
    wait_for_ci_completion,
    wait_for_pr_ci,
    get_ci_timeout_seconds,
    DEFAULT_CI_TIMEOUT_SECONDS,
)


class TestGetLatestWorkflowRun:
    """Tests for get_latest_workflow_run function."""
    
    @patch("tools.github_ci_wait._get")
    def test_returns_latest_run(self, mock_get):
        """Test that it returns the latest workflow run."""
        mock_get.return_value = {
            "workflow_runs": [
                {
                    "id": 123,
                    "status": "completed",
                    "conclusion": "success",
                    "path": ".github/workflows/ci.yml",
                }
            ]
        }
        
        result = get_latest_workflow_run("feature/test-branch")
        
        assert result is not None
        assert result["id"] == 123
        assert result["status"] == "completed"
    
    @patch("tools.github_ci_wait._get")
    def test_returns_none_when_no_runs(self, mock_get):
        """Test that it returns None when no runs found."""
        mock_get.return_value = {"workflow_runs": []}
        
        result = get_latest_workflow_run("feature/test-branch")
        
        assert result is None
    
    @patch("tools.github_ci_wait._get")
    def test_filters_by_workflow_name(self, mock_get):
        """Test that it filters by workflow name when specified."""
        mock_get.return_value = {
            "workflow_runs": [
                {
                    "id": 123,
                    "path": ".github/workflows/ci.yml",
                },
                {
                    "id": 456,
                    "path": ".github/workflows/deploy.yml",
                }
            ]
        }
        
        result = get_latest_workflow_run("main", workflow_name="ci.yml")
        
        assert result is not None
        assert result["id"] == 123


class TestGetWorkflowRunStatus:
    """Tests for get_workflow_run_status function."""
    
    @patch("tools.github_ci_wait._get")
    def test_returns_status_info(self, mock_get):
        """Test that it returns workflow status information."""
        mock_get.return_value = {
            "id": 123,
            "status": "completed",
            "conclusion": "success",
            "html_url": "https://github.com/user/repo/actions/runs/123",
            "name": "CI Pipeline",
        }
        
        result = get_workflow_run_status(123)
        
        assert result["status"] == "completed"
        assert result["conclusion"] == "success"
        assert result["html_url"] == "https://github.com/user/repo/actions/runs/123"
        assert result["id"] == 123


class TestWaitForCICompletion:
    """Tests for wait_for_ci_completion function."""
    
    @patch("tools.github_ci_wait.time.sleep")
    @patch("tools.github_ci_wait.get_workflow_run_status")
    @patch("tools.github_ci_wait.get_latest_workflow_run")
    def test_returns_success_when_ci_passes(self, mock_get_run, mock_get_status, mock_sleep):
        """Test that it returns success when CI passes."""
        mock_get_run.return_value = {"id": 123}
        mock_get_status.return_value = {
            "status": "completed",
            "conclusion": "success",
            "html_url": "https://github.com/user/repo/actions/runs/123",
            "id": 123,
            "name": "CI",
        }
        
        result = wait_for_ci_completion("feature/test", timeout_seconds=60, verbose=False)
        
        assert result["success"] is True
        assert result["status"] == "completed"
        assert result["conclusion"] == "success"
        assert result["timed_out"] is False
    
    @patch("tools.github_ci_wait.time.sleep")
    @patch("tools.github_ci_wait.get_workflow_run_status")
    @patch("tools.github_ci_wait.get_latest_workflow_run")
    def test_returns_failure_when_ci_fails(self, mock_get_run, mock_get_status, mock_sleep):
        """Test that it returns failure when CI fails."""
        mock_get_run.return_value = {"id": 123}
        mock_get_status.return_value = {
            "status": "completed",
            "conclusion": "failure",
            "html_url": "https://github.com/user/repo/actions/runs/123",
            "id": 123,
            "name": "CI",
        }
        
        result = wait_for_ci_completion("feature/test", timeout_seconds=60, verbose=False)
        
        assert result["success"] is False
        assert result["conclusion"] == "failure"
        assert result["timed_out"] is False
    
    @patch("tools.github_ci_wait.time.time")
    @patch("tools.github_ci_wait.time.sleep")
    @patch("tools.github_ci_wait.get_workflow_run_status")
    @patch("tools.github_ci_wait.get_latest_workflow_run")
    def test_returns_timeout_when_time_exceeded(
        self, mock_get_run, mock_get_status, mock_sleep, mock_time
    ):
        """Test that it returns timeout when max time exceeded."""
        # Simulate time passing beyond timeout
        mock_time.side_effect = [0, 5, 61]  # Initial time, after sleep, then past timeout
        
        mock_get_run.return_value = {"id": 123}
        mock_get_status.return_value = {
            "status": "in_progress",
            "conclusion": None,
            "html_url": "https://github.com/user/repo/actions/runs/123",
            "id": 123,
            "name": "CI",
        }
        
        result = wait_for_ci_completion("feature/test", timeout_seconds=60, verbose=False)
        
        assert result["success"] is False
        assert result["timed_out"] is True
        assert result["status"] == "timeout"
    
    @patch("tools.github_ci_wait.time.sleep")
    @patch("tools.github_ci_wait.get_workflow_run_status")
    @patch("tools.github_ci_wait.get_latest_workflow_run")
    def test_waits_for_workflow_to_start(self, mock_get_run, mock_get_status, mock_sleep):
        """Test that it waits when no workflow run exists yet."""
        # First call returns None, second call returns a run
        mock_get_run.side_effect = [None, {"id": 123}]
        mock_get_status.return_value = {
            "status": "completed",
            "conclusion": "success",
            "html_url": "https://github.com/user/repo/actions/runs/123",
            "id": 123,
            "name": "CI",
        }
        
        result = wait_for_ci_completion("feature/test", timeout_seconds=60, verbose=False)
        
        assert result["success"] is True
        # Should have called get_latest_workflow_run at least twice
        assert mock_get_run.call_count >= 2


class TestWaitForPRCI:
    """Tests for wait_for_pr_ci function."""
    
    @patch("tools.github_ci_wait.wait_for_ci_completion")
    @patch("tools.github_ci_wait._get")
    def test_gets_branch_from_pr_and_waits(self, mock_get, mock_wait):
        """Test that it extracts branch from PR and waits for CI."""
        mock_get.return_value = {
            "head": {
                "ref": "feature/test-branch"
            }
        }
        mock_wait.return_value = {
            "success": True,
            "status": "completed",
            "conclusion": "success",
            "timed_out": False,
        }
        
        result = wait_for_pr_ci(42, verbose=False)
        
        assert result["success"] is True
        mock_wait.assert_called_once()
        # Verify it was called with the correct branch
        call_args = mock_wait.call_args
        assert call_args[1]["branch"] == "feature/test-branch"
    
    @patch("tools.github_ci_wait._get")
    def test_returns_error_when_no_head_branch(self, mock_get):
        """Test that it returns error when PR has no head branch."""
        mock_get.return_value = {"head": {}}
        
        result = wait_for_pr_ci(42, verbose=False)
        
        assert result["success"] is False
        assert "Could not determine head branch" in result["conclusion"]


class TestGetCITimeoutSeconds:
    """Tests for get_ci_timeout_seconds function."""
    
    @patch.dict("os.environ", {}, clear=True)
    def test_returns_default_when_not_set(self):
        """Test that it returns default timeout when env var not set."""
        timeout = get_ci_timeout_seconds()
        
        assert timeout == DEFAULT_CI_TIMEOUT_SECONDS
        assert timeout == 1800  # 30 minutes
    
    @patch.dict("os.environ", {"CI_WAIT_TIMEOUT_SECONDS": "3600"})
    def test_returns_custom_timeout_from_env(self):
        """Test that it returns custom timeout from environment."""
        timeout = get_ci_timeout_seconds()
        
        assert timeout == 3600
    
    @patch.dict("os.environ", {"CI_WAIT_TIMEOUT_SECONDS": "invalid"})
    def test_returns_default_when_invalid(self):
        """Test that it returns default when env var is invalid."""
        timeout = get_ci_timeout_seconds()
        
        assert timeout == DEFAULT_CI_TIMEOUT_SECONDS
    
    @patch.dict("os.environ", {"CI_WAIT_TIMEOUT_SECONDS": "-100"})
    def test_returns_default_when_negative(self):
        """Test that it returns default when timeout is negative."""
        timeout = get_ci_timeout_seconds()
        
        assert timeout == DEFAULT_CI_TIMEOUT_SECONDS


class TestCITimeoutChange:
    """Tests to verify the timeout change from 15 to 30 minutes (SDT1-64)."""
    
    def test_default_timeout_is_30_minutes(self):
        """Test that default CI timeout is now 30 minutes (was 15 minutes)."""
        assert DEFAULT_CI_TIMEOUT_SECONDS == 1800  # 30 minutes
        assert DEFAULT_CI_TIMEOUT_SECONDS == 30 * 60
        
        # Verify it's not the old value
        assert DEFAULT_CI_TIMEOUT_SECONDS != 900  # Not 15 minutes
