"""
test_orchestrator_ci_monitor.py
────────────────────────────────
Tests for the Orchestrator CI monitor module.

Tests verify:
- CI monitor initialization
- Workflow status polling
- Timeout handling (30 minute timeout)
- Success/failure/cancelled status detection
- Retry logic for transient errors
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys

# Add agents directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../agents"))

from orchestrator_ci_monitor import (
    CIMonitor,
    CITimeoutError,
    CI_WAIT_TIMEOUT_MINUTES,
    CI_POLL_INTERVAL_SECONDS,
    wait_for_ci_completion,
)


class TestCIMonitorInit:
    """Test CIMonitor initialization."""
    
    def test_init_with_token(self):
        """Test initialization with explicit token."""
        monitor = CIMonitor(github_token="test-token")
        assert monitor.github_token == "test-token"
        assert monitor.timeout_minutes == CI_WAIT_TIMEOUT_MINUTES
        assert monitor.poll_interval_seconds == CI_POLL_INTERVAL_SECONDS
        assert monitor.verbose is True
    
    def test_init_with_env_token(self, monkeypatch):
        """Test initialization with environment variable token."""
        monkeypatch.setenv("GITHUB_TOKEN", "env-token")
        monitor = CIMonitor()
        assert monitor.github_token == "env-token"
    
    def test_init_without_token(self, monkeypatch):
        """Test initialization fails without token."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with pytest.raises(ValueError, match="GitHub token required"):
            CIMonitor(github_token=None)
    
    def test_init_custom_timeout(self):
        """Test initialization with custom timeout."""
        monitor = CIMonitor(github_token="test-token", timeout_minutes=45)
        assert monitor.timeout_minutes == 45
    
    def test_init_custom_poll_interval(self):
        """Test initialization with custom poll interval."""
        monitor = CIMonitor(github_token="test-token", poll_interval_seconds=60)
        assert monitor.poll_interval_seconds == 60
    
    def test_init_verbose_false(self):
        """Test initialization with verbose disabled."""
        monitor = CIMonitor(github_token="test-token", verbose=False)
        assert monitor.verbose is False


class TestCIMonitorLog:
    """Test CIMonitor logging."""
    
    def test_log_when_verbose(self, capsys):
        """Test logging when verbose is True."""
        monitor = CIMonitor(github_token="test-token", verbose=True)
        monitor.log("Test message")
        captured = capsys.readouterr()
        assert "Test message" in captured.out
        assert "CI-MONITOR" in captured.out
    
    def test_log_when_not_verbose(self, capsys):
        """Test no logging when verbose is False."""
        monitor = CIMonitor(github_token="test-token", verbose=False)
        monitor.log("Test message")
        captured = capsys.readouterr()
        assert captured.out == ""


class TestGetWorkflowRuns:
    """Test getting workflow runs from GitHub API."""
    
    @patch("orchestrator_ci_monitor.requests.get")
    def test_get_workflow_runs_success(self, mock_get):
        """Test successful workflow runs retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "workflow_runs": [
                {"id": 123, "status": "completed"},
                {"id": 124, "status": "in_progress"},
            ]
        }
        mock_get.return_value = mock_response
        
        monitor = CIMonitor(github_token="test-token")
        runs = monitor.get_workflow_runs("owner", "repo", "main")
        
        assert len(runs) == 2
        assert runs[0]["id"] == 123
        assert runs[1]["id"] == 124
        
        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "owner/repo" in call_args[0][0]
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-token"
        assert call_args[1]["params"]["branch"] == "main"
    
    @patch("orchestrator_ci_monitor.requests.get")
    def test_get_workflow_runs_with_commit_sha(self, mock_get):
        """Test workflow runs retrieval with commit SHA filter."""
        mock_response = Mock()
        mock_response.json.return_value = {"workflow_runs": []}
        mock_get.return_value = mock_response
        
        monitor = CIMonitor(github_token="test-token")
        monitor.get_workflow_runs("owner", "repo", "main", commit_sha="abc123")
        
        call_args = mock_get.call_args
        assert call_args[1]["params"]["head_sha"] == "abc123"
    
    @patch("orchestrator_ci_monitor.requests.get")
    def test_get_workflow_runs_api_error(self, mock_get):
        """Test handling of API errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_get.return_value = mock_response
        
        monitor = CIMonitor(github_token="test-token")
        with pytest.raises(Exception, match="API Error"):
            monitor.get_workflow_runs("owner", "repo", "main")


class TestGetWorkflowRunStatus:
    """Test getting workflow run status."""
    
    @patch("orchestrator_ci_monitor.requests.get")
    def test_get_workflow_run_status_completed(self, mock_get):
        """Test getting status of completed run."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": 123,
            "status": "completed",
            "conclusion": "success",
            "html_url": "https://github.com/owner/repo/actions/runs/123",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:05:00Z",
        }
        mock_get.return_value = mock_response
        
        monitor = CIMonitor(github_token="test-token")
        status = monitor.get_workflow_run_status("owner", "repo", 123)
        
        assert status["id"] == 123
        assert status["status"] == "completed"
        assert status["conclusion"] == "success"
        assert "html_url" in status
    
    @patch("orchestrator_ci_monitor.requests.get")
    def test_get_workflow_run_status_in_progress(self, mock_get):
        """Test getting status of in-progress run."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": 123,
            "status": "in_progress",
            "html_url": "https://github.com/owner/repo/actions/runs/123",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:02:00Z",
        }
        mock_get.return_value = mock_response
        
        monitor = CIMonitor(github_token="test-token")
        status = monitor.get_workflow_run_status("owner", "repo", 123)
        
        assert status["status"] == "in_progress"
        assert status["conclusion"] is None


class TestWaitForCI:
    """Test waiting for CI completion."""
    
    @patch("orchestrator_ci_monitor.time.sleep")
    @patch("orchestrator_ci_monitor.CIMonitor.get_workflow_run_status")
    @patch("orchestrator_ci_monitor.CIMonitor.get_workflow_runs")
    def test_wait_for_ci_success(self, mock_get_runs, mock_get_status, mock_sleep):
        """Test waiting for successful CI completion."""
        # Mock finding the run
        mock_get_runs.return_value = [{"id": 123}]
        
        # Mock status progression: in_progress -> completed with success
        mock_get_status.side_effect = [
            {"id": 123, "status": "in_progress", "conclusion": None, "html_url": "url", "created_at": "t", "updated_at": "t"},
            {"id": 123, "status": "completed", "conclusion": "success", "html_url": "url", "created_at": "t", "updated_at": "t"},
        ]
        
        monitor = CIMonitor(github_token="test-token", poll_interval_seconds=1)
        result = monitor.wait_for_ci("owner", "repo", "main")
        
        assert result == "success"
        assert mock_sleep.call_count == 1
    
    @patch("orchestrator_ci_monitor.time.sleep")
    @patch("orchestrator_ci_monitor.CIMonitor.get_workflow_run_status")
    def test_wait_for_ci_failure(self, mock_get_status, mock_sleep):
        """Test waiting for failed CI."""
        mock_get_status.return_value = {
            "id": 123,
            "status": "completed",
            "conclusion": "failure",
            "html_url": "url",
            "created_at": "t",
            "updated_at": "t",
        }
        
        monitor = CIMonitor(github_token="test-token", poll_interval_seconds=1)
        result = monitor.wait_for_ci("owner", "repo", "main", run_id=123)
        
        assert result == "failure"
    
    @patch("orchestrator_ci_monitor.time.sleep")
    @patch("orchestrator_ci_monitor.CIMonitor.get_workflow_run_status")
    def test_wait_for_ci_cancelled(self, mock_get_status, mock_sleep):
        """Test waiting for cancelled CI."""
        mock_get_status.return_value = {
            "id": 123,
            "status": "completed",
            "conclusion": "cancelled",
            "html_url": "url",
            "created_at": "t",
            "updated_at": "t",
        }
        
        monitor = CIMonitor(github_token="test-token", poll_interval_seconds=1)
        result = monitor.wait_for_ci("owner", "repo", "main", run_id=123)
        
        assert result == "cancelled"
    
    @patch("orchestrator_ci_monitor.datetime")
    @patch("orchestrator_ci_monitor.time.sleep")
    @patch("orchestrator_ci_monitor.CIMonitor.get_workflow_run_status")
    def test_wait_for_ci_timeout(self, mock_get_status, mock_sleep, mock_datetime):
        """Test CI timeout after 30 minutes."""
        # Mock time to simulate timeout
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        timeout_time = start_time + timedelta(minutes=31)  # Exceed 30 minute timeout
        
        mock_datetime.utcnow.side_effect = [start_time, start_time, timeout_time]
        
        mock_get_status.return_value = {
            "id": 123,
            "status": "in_progress",
            "conclusion": None,
            "html_url": "url",
            "created_at": "t",
            "updated_at": "t",
        }
        
        monitor = CIMonitor(github_token="test-token", timeout_minutes=30, poll_interval_seconds=1)
        
        with pytest.raises(CITimeoutError, match="exceeded timeout of 30 minutes"):
            monitor.wait_for_ci("owner", "repo", "main", run_id=123)
    
    @patch("orchestrator_ci_monitor.CIMonitor.get_workflow_runs")
    def test_wait_for_ci_no_runs_found(self, mock_get_runs):
        """Test error when no workflow runs found."""
        mock_get_runs.return_value = []
        
        monitor = CIMonitor(github_token="test-token")
        
        with pytest.raises(ValueError, match="No workflow runs found"):
            monitor.wait_for_ci("owner", "repo", "main")
    
    @patch("orchestrator_ci_monitor.time.sleep")
    @patch("orchestrator_ci_monitor.CIMonitor.get_workflow_run_status")
    def test_wait_for_ci_with_commit_sha(self, mock_get_status, mock_sleep):
        """Test waiting for CI with specific commit SHA."""
        mock_get_status.return_value = {
            "id": 123,
            "status": "completed",
            "conclusion": "success",
            "html_url": "url",
            "created_at": "t",
            "updated_at": "t",
        }
        
        monitor = CIMonitor(github_token="test-token")
        result = monitor.wait_for_ci("owner", "repo", "main", commit_sha="abc123", run_id=123)
        
        assert result == "success"


class TestWaitForCIWithRetry:
    """Test waiting for CI with retry logic."""
    
    @patch("orchestrator_ci_monitor.time.sleep")
    @patch("orchestrator_ci_monitor.CIMonitor.wait_for_ci")
    def test_wait_for_ci_with_retry_success(self, mock_wait_for_ci, mock_sleep):
        """Test successful CI wait with retry."""
        mock_wait_for_ci.return_value = "success"
        
        monitor = CIMonitor(github_token="test-token")
        result = monitor.wait_for_ci_with_retry("owner", "repo", "main", run_id=123)
        
        assert result == "success"
        assert mock_wait_for_ci.call_count == 1
    
    @patch("orchestrator_ci_monitor.time.sleep")
    @patch("orchestrator_ci_monitor.CIMonitor.wait_for_ci")
    def test_wait_for_ci_with_retry_timeout(self, mock_wait_for_ci, mock_sleep):
        """Test timeout handling with retry."""
        mock_wait_for_ci.side_effect = CITimeoutError("Timeout")
        
        monitor = CIMonitor(github_token="test-token")
        result = monitor.wait_for_ci_with_retry("owner", "repo", "main", run_id=123)
        
        assert result == "timeout"
        assert mock_wait_for_ci.call_count == 1
    
    @patch("orchestrator_ci_monitor.time.sleep")
    @patch("orchestrator_ci_monitor.CIMonitor.wait_for_ci")
    @patch("orchestrator_ci_monitor.requests.HTTPError")
    def test_wait_for_ci_with_retry_transient_error(self, mock_http_error, mock_wait_for_ci, mock_sleep):
        """Test retry on transient HTTP errors."""
        import requests
        
        # First two attempts fail, third succeeds
        mock_wait_for_ci.side_effect = [
            requests.HTTPError("Transient error"),
            requests.HTTPError("Transient error"),
            "success",
        ]
        
        monitor = CIMonitor(github_token="test-token")
        result = monitor.wait_for_ci_with_retry("owner", "repo", "main", run_id=123, max_retries=3)
        
        assert result == "success"
        assert mock_wait_for_ci.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep between retries
    
    @patch("orchestrator_ci_monitor.time.sleep")
    @patch("orchestrator_ci_monitor.CIMonitor.wait_for_ci")
    def test_wait_for_ci_with_retry_max_retries_exceeded(self, mock_wait_for_ci, mock_sleep):
        """Test failure after max retries exceeded."""
        import requests
        
        mock_wait_for_ci.side_effect = requests.HTTPError("Persistent error")
        
        monitor = CIMonitor(github_token="test-token")
        
        with pytest.raises(requests.HTTPError, match="Persistent error"):
            monitor.wait_for_ci_with_retry("owner", "repo", "main", run_id=123, max_retries=3)
        
        assert mock_wait_for_ci.call_count == 3


class TestConvenienceFunction:
    """Test convenience function for CI waiting."""
    
    @patch("orchestrator_ci_monitor.CIMonitor")
    def test_wait_for_ci_completion(self, mock_monitor_class):
        """Test convenience function creates monitor and waits."""
        mock_monitor = Mock()
        mock_monitor.wait_for_ci_with_retry.return_value = "success"
        mock_monitor_class.return_value = mock_monitor
        
        result = wait_for_ci_completion(
            repo_owner="owner",
            repo_name="repo",
            branch="main",
            timeout_minutes=30,
            github_token="test-token",
        )
        
        assert result == "success"
        mock_monitor_class.assert_called_once_with(
            github_token="test-token",
            timeout_minutes=30,
            verbose=True,
        )
        mock_monitor.wait_for_ci_with_retry.assert_called_once()


class TestTimeoutConfiguration:
    """Test that the timeout is correctly set to 30 minutes."""
    
    def test_default_timeout_is_30_minutes(self):
        """Verify default timeout is 30 minutes (SDT1-64)."""
        assert CI_WAIT_TIMEOUT_MINUTES == 30
    
    def test_monitor_uses_default_timeout(self):
        """Verify monitor uses 30 minute default."""
        monitor = CIMonitor(github_token="test-token")
        assert monitor.timeout_minutes == 30
    
    def test_poll_interval_is_30_seconds(self):
        """Verify default poll interval is 30 seconds."""
        assert CI_POLL_INTERVAL_SECONDS == 30
    
    def test_monitor_uses_default_poll_interval(self):
        """Verify monitor uses 30 second poll interval."""
        monitor = CIMonitor(github_token="test-token")
        assert monitor.poll_interval_seconds == 30
