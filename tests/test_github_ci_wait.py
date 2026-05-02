"""
tests/test_github_ci_wait.py
────────────────────────────
Tests for GitHub CI wait functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from tools.github_client import (
    get_commit_status,
    get_check_runs,
    get_combined_ci_status,
    wait_for_ci_completion,
    wait_for_pr_ci,
    CI_WAIT_TIMEOUT_SECONDS,
    CI_POLL_INTERVAL_SECONDS,
)


class TestCIStatusFunctions:
    """Test CI status checking functions."""
    
    @patch('tools.github_client._get')
    def test_get_commit_status(self, mock_get):
        """Test getting commit status."""
        mock_get.return_value = {
            "state": "success",
            "statuses": [
                {"context": "ci/test", "state": "success"},
                {"context": "ci/lint", "state": "success"},
            ],
            "total_count": 2,
        }
        
        result = get_commit_status("abc123")
        
        assert result["state"] == "success"
        assert result["total_count"] == 2
        assert len(result["statuses"]) == 2
        mock_get.assert_called_once()
    
    @patch('tools.github_client._get')
    def test_get_check_runs(self, mock_get):
        """Test getting check runs."""
        mock_get.return_value = {
            "total_count": 2,
            "check_runs": [
                {
                    "name": "Build",
                    "status": "completed",
                    "conclusion": "success",
                },
                {
                    "name": "Test",
                    "status": "completed",
                    "conclusion": "success",
                },
            ],
        }
        
        result = get_check_runs("abc123")
        
        assert result["total_count"] == 2
        assert len(result["check_runs"]) == 2
        mock_get.assert_called_once()
    
    @patch('tools.github_client.get_check_runs')
    @patch('tools.github_client.get_commit_status')
    def test_get_combined_ci_status_all_success(self, mock_status, mock_checks):
        """Test combined status when all checks pass."""
        mock_status.return_value = {
            "state": "success",
            "statuses": [{"context": "ci/test", "state": "success"}],
            "total_count": 1,
        }
        mock_checks.return_value = {
            "total_count": 1,
            "check_runs": [{
                "name": "Build",
                "status": "completed",
                "conclusion": "success",
            }],
        }
        
        result = get_combined_ci_status("abc123")
        
        assert result["state"] == "success"
        assert result["all_passed"] is True
        assert result["total_checks"] == 2
    
    @patch('tools.github_client.get_check_runs')
    @patch('tools.github_client.get_commit_status')
    def test_get_combined_ci_status_with_failure(self, mock_status, mock_checks):
        """Test combined status when a check fails."""
        mock_status.return_value = {
            "state": "failure",
            "statuses": [{"context": "ci/test", "state": "failure"}],
            "total_count": 1,
        }
        mock_checks.return_value = {
            "total_count": 0,
            "check_runs": [],
        }
        
        result = get_combined_ci_status("abc123")
        
        assert result["state"] == "failure"
        assert result["all_passed"] is False
    
    @patch('tools.github_client.get_check_runs')
    @patch('tools.github_client.get_commit_status')
    def test_get_combined_ci_status_pending(self, mock_status, mock_checks):
        """Test combined status when checks are pending."""
        mock_status.return_value = {
            "state": "pending",
            "statuses": [{"context": "ci/test", "state": "pending"}],
            "total_count": 1,
        }
        mock_checks.return_value = {
            "total_count": 1,
            "check_runs": [{
                "name": "Build",
                "status": "in_progress",
                "conclusion": None,
            }],
        }
        
        result = get_combined_ci_status("abc123")
        
        assert result["state"] == "pending"
        assert result["all_passed"] is False


class TestCIWaitFunctions:
    """Test CI wait functionality."""
    
    @patch('tools.github_client.time.sleep')
    @patch('tools.github_client.get_combined_ci_status')
    def test_wait_for_ci_completion_immediate_success(self, mock_status, mock_sleep):
        """Test waiting when CI passes immediately."""
        mock_status.return_value = {
            "state": "success",
            "all_passed": True,
            "checks": [{"name": "Test", "type": "status", "state": "success"}],
            "total_checks": 1,
        }
        
        result = wait_for_ci_completion("abc123", verbose=False)
        
        assert result["completed"] is True
        assert result["timed_out"] is False
        assert result["all_passed"] is True
        assert result["state"] == "success"
        mock_sleep.assert_not_called()
    
    @patch('tools.github_client.time.sleep')
    @patch('tools.github_client.get_combined_ci_status')
    def test_wait_for_ci_completion_eventual_success(self, mock_status, mock_sleep):
        """Test waiting when CI eventually passes."""
        # First call: pending, second call: success
        mock_status.side_effect = [
            {
                "state": "pending",
                "all_passed": False,
                "checks": [{"name": "Test", "type": "status", "state": "pending"}],
                "total_checks": 1,
            },
            {
                "state": "success",
                "all_passed": True,
                "checks": [{"name": "Test", "type": "status", "state": "success"}],
                "total_checks": 1,
            },
        ]
        
        result = wait_for_ci_completion("abc123", timeout_seconds=120, verbose=False)
        
        assert result["completed"] is True
        assert result["timed_out"] is False
        assert result["all_passed"] is True
        mock_sleep.assert_called()
    
    @patch('tools.github_client.time.sleep')
    @patch('tools.github_client.get_combined_ci_status')
    def test_wait_for_ci_completion_failure(self, mock_status, mock_sleep):
        """Test waiting when CI fails."""
        mock_status.return_value = {
            "state": "failure",
            "all_passed": False,
            "checks": [{"name": "Test", "type": "status", "state": "failure"}],
            "total_checks": 1,
        }
        
        result = wait_for_ci_completion("abc123", verbose=False)
        
        assert result["completed"] is True
        assert result["timed_out"] is False
        assert result["all_passed"] is False
        assert result["state"] == "failure"
    
    @patch('tools.github_client.time.time')
    @patch('tools.github_client.time.sleep')
    @patch('tools.github_client.get_combined_ci_status')
    def test_wait_for_ci_completion_timeout(self, mock_status, mock_sleep, mock_time):
        """Test waiting times out."""
        # Mock time to simulate timeout
        mock_time.side_effect = [
            0,      # start_time
            0,      # first elapsed check
            100,    # after first sleep
            200,    # timeout check (exceeds 60s timeout)
            200,    # duration calculation
        ]
        
        mock_status.return_value = {
            "state": "pending",
            "all_passed": False,
            "checks": [{"name": "Test", "type": "status", "state": "pending"}],
            "total_checks": 1,
        }
        
        result = wait_for_ci_completion("abc123", timeout_seconds=60, verbose=False)
        
        assert result["completed"] is False
        assert result["timed_out"] is True
        assert result["all_passed"] is False
    
    @patch('tools.github_client.wait_for_ci_completion')
    @patch('tools.github_client._get')
    def test_wait_for_pr_ci(self, mock_get, mock_wait):
        """Test waiting for PR CI."""
        mock_get.return_value = {
            "number": 123,
            "title": "Test PR",
            "head": {"sha": "abc123def456"},
        }
        mock_wait.return_value = {
            "completed": True,
            "timed_out": False,
            "all_passed": True,
            "state": "success",
            "duration_seconds": 120.5,
            "checks": [],
        }
        
        result = wait_for_pr_ci(123, verbose=False)
        
        assert result["completed"] is True
        assert result["all_passed"] is True
        mock_get.assert_called_once()
        mock_wait.assert_called_once_with(
            "abc123def456",
            CI_WAIT_TIMEOUT_SECONDS,
            CI_POLL_INTERVAL_SECONDS,
            False,
        )


class TestCITimeoutConfiguration:
    """Test CI timeout configuration values."""
    
    def test_ci_wait_timeout_is_30_minutes(self):
        """Verify CI wait timeout is set to 30 minutes."""
        expected_seconds = 30 * 60  # 30 minutes
        assert CI_WAIT_TIMEOUT_SECONDS == expected_seconds
        assert CI_WAIT_TIMEOUT_SECONDS == 1800
    
    def test_ci_poll_interval_is_30_seconds(self):
        """Verify CI poll interval is 30 seconds."""
        assert CI_POLL_INTERVAL_SECONDS == 30
