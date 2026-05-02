"""
tests/test_ci_wait.py
─────────────────────
Unit tests for CI wait functionality.

Tests the CI wait timeout extension from 15 to 30 minutes (SDT1-64)
and related functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time
from tools.ci_wait import (
    CI_WAIT_TIMEOUT_SECONDS,
    CI_POLL_INTERVAL_SECONDS,
    CheckStatus,
    CheckConclusion,
    CIWaitResult,
    get_pr_head_sha,
    get_commit_check_runs,
    get_commit_status,
    are_checks_complete,
    wait_for_ci,
    wait_for_ci_by_branch,
    get_ci_summary,
)


# ── Configuration Tests ───────────────────────────────────────────────────────


def test_ci_timeout_is_30_minutes():
    """Test that CI wait timeout is set to 30 minutes (1800 seconds)."""
    assert CI_WAIT_TIMEOUT_SECONDS == 1800, (
        "CI_WAIT_TIMEOUT_SECONDS should be 30 minutes (1800 seconds) per SDT1-64"
    )


def test_ci_timeout_increased_from_15_minutes():
    """Verify timeout was increased from 15 to 30 minutes."""
    # This documents the change: old value was 15*60 = 900 seconds
    old_timeout = 15 * 60
    new_timeout = CI_WAIT_TIMEOUT_SECONDS
    
    assert new_timeout == 30 * 60, "New timeout should be 30 minutes"
    assert new_timeout > old_timeout, "Timeout should have been increased"
    assert new_timeout == old_timeout * 2, "Timeout should be doubled from 15 to 30 minutes"


def test_poll_interval_is_reasonable():
    """Test that poll interval is set to a reasonable value."""
    assert CI_POLL_INTERVAL_SECONDS == 30, "Poll interval should be 30 seconds"
    assert CI_POLL_INTERVAL_SECONDS > 0, "Poll interval must be positive"
    assert CI_POLL_INTERVAL_SECONDS <= 60, "Poll interval should not exceed 1 minute"


# ── Enum Tests ────────────────────────────────────────────────────────────────


def test_check_status_enum_values():
    """Test CheckStatus enum has expected values."""
    assert CheckStatus.QUEUED.value == "queued"
    assert CheckStatus.IN_PROGRESS.value == "in_progress"
    assert CheckStatus.COMPLETED.value == "completed"


def test_check_conclusion_enum_values():
    """Test CheckConclusion enum has expected values."""
    assert CheckConclusion.SUCCESS.value == "success"
    assert CheckConclusion.FAILURE.value == "failure"
    assert CheckConclusion.NEUTRAL.value == "neutral"
    assert CheckConclusion.CANCELLED.value == "cancelled"
    assert CheckConclusion.SKIPPED.value == "skipped"
    assert CheckConclusion.TIMED_OUT.value == "timed_out"
    assert CheckConclusion.ACTION_REQUIRED.value == "action_required"


# ── CIWaitResult Tests ────────────────────────────────────────────────────────


def test_ci_wait_result_creation():
    """Test CIWaitResult can be created with expected parameters."""
    result = CIWaitResult(
        success=True,
        timeout=False,
        duration_seconds=120.5,
        check_runs=[{"name": "test", "status": "completed"}],
        message="All checks passed",
    )
    
    assert result.success is True
    assert result.timeout is False
    assert result.duration_seconds == 120.5
    assert len(result.check_runs) == 1
    assert result.message == "All checks passed"


def test_ci_wait_result_repr():
    """Test CIWaitResult string representation."""
    result = CIWaitResult(
        success=True,
        timeout=False,
        duration_seconds=123.4,
        check_runs=[{"name": "test"}],
        message="Success",
    )
    
    repr_str = repr(result)
    assert "SUCCESS" in repr_str
    assert "123.4" in repr_str
    assert "1 checks" in repr_str


def test_ci_wait_result_timeout_repr():
    """Test CIWaitResult representation for timeout."""
    result = CIWaitResult(
        success=False,
        timeout=True,
        duration_seconds=1800.0,
        check_runs=[],
        message="Timeout",
    )
    
    repr_str = repr(result)
    assert "TIMEOUT" in repr_str
    assert "1800.0" in repr_str


def test_ci_wait_result_failure_repr():
    """Test CIWaitResult representation for failure."""
    result = CIWaitResult(
        success=False,
        timeout=False,
        duration_seconds=60.0,
        check_runs=[{"name": "test", "conclusion": "failure"}],
        message="Check failed",
    )
    
    repr_str = repr(result)
    assert "FAILURE" in repr_str


# ── API Function Tests ────────────────────────────────────────────────────────


@patch("tools.ci_wait.requests.get")
def test_get_pr_head_sha_success(mock_get):
    """Test getting PR HEAD SHA."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = {
        "head": {"sha": "abc123def456"}
    }
    mock_get.return_value = mock_response
    
    sha = get_pr_head_sha(42)
    
    assert sha == "abc123def456"
    mock_get.assert_called_once()


@patch("tools.ci_wait.requests.get")
def test_get_pr_head_sha_failure(mock_get):
    """Test getting PR HEAD SHA when PR not found."""
    mock_get.side_effect = Exception("404 Not Found")
    
    sha = get_pr_head_sha(999)
    
    assert sha is None


@patch("tools.ci_wait.requests.get")
def test_get_commit_check_runs_success(mock_get):
    """Test getting commit check runs."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = {
        "check_runs": [
            {"name": "test", "status": "completed", "conclusion": "success"},
            {"name": "lint", "status": "completed", "conclusion": "success"},
        ]
    }
    mock_get.return_value = mock_response
    
    check_runs = get_commit_check_runs("abc123")
    
    assert len(check_runs) == 2
    assert check_runs[0]["name"] == "test"
    assert check_runs[1]["name"] == "lint"


@patch("tools.ci_wait.requests.get")
def test_get_commit_check_runs_empty(mock_get):
    """Test getting check runs when none exist."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = {"check_runs": []}
    mock_get.return_value = mock_response
    
    check_runs = get_commit_check_runs("abc123")
    
    assert check_runs == []


@patch("tools.ci_wait.requests.get")
def test_get_commit_status(mock_get):
    """Test getting commit status."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = {
        "state": "success",
        "statuses": []
    }
    mock_get.return_value = mock_response
    
    status = get_commit_status("abc123")
    
    assert status["state"] == "success"


# ── Check Completion Tests ────────────────────────────────────────────────────


@patch("tools.ci_wait.get_commit_check_runs")
@patch("tools.ci_wait.get_commit_status")
def test_are_checks_complete_all_passed(mock_status, mock_check_runs):
    """Test checks are complete when all pass."""
    mock_check_runs.return_value = [
        {"name": "test", "status": "completed", "conclusion": "success"},
        {"name": "lint", "status": "completed", "conclusion": "success"},
    ]
    mock_status.return_value = {"state": "success"}
    
    complete, check_runs, summary = are_checks_complete("abc123")
    
    assert complete is True
    assert "All 2 checks passed" in summary


@patch("tools.ci_wait.get_commit_check_runs")
@patch("tools.ci_wait.get_commit_status")
def test_are_checks_complete_with_failure(mock_status, mock_check_runs):
    """Test checks are complete but failed."""
    mock_check_runs.return_value = [
        {"name": "test", "status": "completed", "conclusion": "success"},
        {"name": "lint", "status": "completed", "conclusion": "failure"},
    ]
    mock_status.return_value = {"state": "failure"}
    
    complete, check_runs, summary = are_checks_complete("abc123")
    
    assert complete is True
    assert "failed" in summary.lower()


@patch("tools.ci_wait.get_commit_check_runs")
@patch("tools.ci_wait.get_commit_status")
def test_are_checks_complete_still_running(mock_status, mock_check_runs):
    """Test checks are not complete when still running."""
    mock_check_runs.return_value = [
        {"name": "test", "status": "completed", "conclusion": "success"},
        {"name": "lint", "status": "in_progress", "conclusion": None},
    ]
    mock_status.return_value = {"state": "pending"}
    
    complete, check_runs, summary = are_checks_complete("abc123")
    
    assert complete is False
    assert "in progress" in summary.lower()
    assert "lint" in summary


@patch("tools.ci_wait.get_commit_check_runs")
@patch("tools.ci_wait.get_commit_status")
def test_are_checks_complete_skipped_is_ok(mock_status, mock_check_runs):
    """Test that skipped checks are treated as passing."""
    mock_check_runs.return_value = [
        {"name": "test", "status": "completed", "conclusion": "success"},
        {"name": "optional", "status": "completed", "conclusion": "skipped"},
    ]
    mock_status.return_value = {"state": "success"}
    
    complete, check_runs, summary = are_checks_complete("abc123")
    
    assert complete is True
    assert "passed" in summary.lower()


@patch("tools.ci_wait.get_commit_check_runs")
@patch("tools.ci_wait.get_commit_status")
def test_are_checks_complete_no_check_runs_pending(mock_status, mock_check_runs):
    """Test when no check runs exist and status is pending."""
    mock_check_runs.return_value = []
    mock_status.return_value = {"state": "pending"}
    
    complete, check_runs, summary = are_checks_complete("abc123")
    
    assert complete is False
    assert "waiting" in summary.lower()


# ── Wait for CI Tests ─────────────────────────────────────────────────────────


@patch("tools.ci_wait.get_pr_head_sha")
@patch("tools.ci_wait.are_checks_complete")
@patch("tools.ci_wait.get_commit_check_runs")
@patch("tools.ci_wait.time.sleep")
def test_wait_for_ci_success_immediate(mock_sleep, mock_get_runs, mock_checks, mock_sha):
    """Test waiting for CI when checks pass immediately."""
    mock_sha.return_value = "abc123"
    mock_checks.return_value = (True, [{"name": "test", "conclusion": "success"}], "All checks passed")
    mock_get_runs.return_value = [{"name": "test", "conclusion": "success"}]
    
    result = wait_for_ci(42, verbose=False)
    
    assert result.success is True
    assert result.timeout is False
    assert result.duration_seconds < 1
    mock_sleep.assert_not_called()


@patch("tools.ci_wait.get_pr_head_sha")
@patch("tools.ci_wait.are_checks_complete")
@patch("tools.ci_wait.get_commit_check_runs")
@patch("tools.ci_wait.time.sleep")
def test_wait_for_ci_success_after_wait(mock_sleep, mock_get_runs, mock_checks, mock_sha):
    """Test waiting for CI when checks pass after polling."""
    mock_sha.return_value = "abc123"
    # First call: checks not complete, second call: checks complete
    mock_checks.side_effect = [
        (False, [], "Checks in progress"),
        (True, [{"name": "test", "conclusion": "success"}], "All checks passed"),
    ]
    mock_get_runs.return_value = [{"name": "test", "conclusion": "success"}]
    
    result = wait_for_ci(42, poll_interval=1, verbose=False)
    
    assert result.success is True
    assert result.timeout is False
    mock_sleep.assert_called_once()


@patch("tools.ci_wait.get_pr_head_sha")
@patch("tools.ci_wait.are_checks_complete")
@patch("tools.ci_wait.get_commit_check_runs")
@patch("tools.ci_wait.time.sleep")
@patch("tools.ci_wait.time.time")
def test_wait_for_ci_timeout(mock_time, mock_sleep, mock_get_runs, mock_checks, mock_sha):
    """Test waiting for CI times out after configured duration."""
    mock_sha.return_value = "abc123"
    mock_checks.return_value = (False, [], "Checks still in progress")
    mock_get_runs.return_value = []
    
    # Simulate time passing
    start_time = 1000.0
    timeout_seconds = 10
    mock_time.side_effect = [
        start_time,  # Start
        start_time + timeout_seconds + 1,  # After timeout
    ]
    
    result = wait_for_ci(42, timeout_seconds=timeout_seconds, verbose=False)
    
    assert result.success is False
    assert result.timeout is True
    assert "timeout" in result.message.lower()


@patch("tools.ci_wait.get_pr_head_sha")
def test_wait_for_ci_pr_not_found(mock_sha):
    """Test waiting for CI when PR cannot be found."""
    mock_sha.return_value = None
    
    result = wait_for_ci(999, verbose=False)
    
    assert result.success is False
    assert result.timeout is False
    assert "Failed to get PR" in result.message


@patch("tools.ci_wait.get_pr_head_sha")
@patch("tools.ci_wait.are_checks_complete")
@patch("tools.ci_wait.get_commit_check_runs")
@patch("tools.ci_wait.time.sleep")
def test_wait_for_ci_checks_fail(mock_sleep, mock_get_runs, mock_checks, mock_sha):
    """Test waiting for CI when checks fail."""
    mock_sha.return_value = "abc123"
    mock_checks.return_value = (True, [{"name": "test", "conclusion": "failure"}], "Checks failed")
    mock_get_runs.return_value = [{"name": "test", "conclusion": "failure"}]
    
    result = wait_for_ci(42, verbose=False)
    
    assert result.success is False
    assert result.timeout is False
    assert len(result.check_runs) > 0


@patch("tools.ci_wait.requests.get")
@patch("tools.ci_wait.wait_for_ci")
def test_wait_for_ci_by_branch_success(mock_wait, mock_get):
    """Test waiting for CI by branch name."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = [{"number": 42}]
    mock_get.return_value = mock_response
    
    mock_wait.return_value = CIWaitResult(
        success=True,
        timeout=False,
        duration_seconds=60.0,
        check_runs=[],
        message="Success",
    )
    
    result = wait_for_ci_by_branch("feature/test", verbose=False)
    
    assert result.success is True
    mock_wait.assert_called_once_with(42, CI_WAIT_TIMEOUT_SECONDS, CI_POLL_INTERVAL_SECONDS, False)


@patch("tools.ci_wait.requests.get")
def test_wait_for_ci_by_branch_no_pr(mock_get):
    """Test waiting for CI by branch when no PR exists."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = []
    mock_get.return_value = mock_response
    
    result = wait_for_ci_by_branch("feature/test", verbose=False)
    
    assert result.success is False
    assert "No open PR found" in result.message


# ── CI Summary Tests ──────────────────────────────────────────────────────────


@patch("tools.ci_wait.get_pr_head_sha")
@patch("tools.ci_wait.are_checks_complete")
def test_get_ci_summary(mock_checks, mock_sha):
    """Test getting CI summary."""
    mock_sha.return_value = "abc123"
    mock_checks.return_value = (
        True,
        [
            {"name": "test", "status": "completed", "conclusion": "success"},
            {"name": "lint", "status": "completed", "conclusion": "success"},
        ],
        "All checks passed",
    )
    
    summary = get_ci_summary(42)
    
    assert "PR #42" in summary
    assert "test" in summary
    assert "lint" in summary
    assert "passed" in summary.lower()


@patch("tools.ci_wait.get_pr_head_sha")
def test_get_ci_summary_pr_not_found(mock_sha):
    """Test getting CI summary when PR not found."""
    mock_sha.return_value = None
    
    summary = get_ci_summary(999)
    
    assert "Could not get PR" in summary


@patch("tools.ci_wait.get_pr_head_sha")
@patch("tools.ci_wait.are_checks_complete")
def test_get_ci_summary_with_in_progress(mock_checks, mock_sha):
    """Test getting CI summary with checks in progress."""
    mock_sha.return_value = "abc123"
    mock_checks.return_value = (
        False,
        [
            {"name": "test", "status": "completed", "conclusion": "success"},
            {"name": "lint", "status": "in_progress", "conclusion": None},
        ],
        "Checks in progress",
    )
    
    summary = get_ci_summary(42)
    
    assert "PR #42" in summary
    assert "in_progress" in summary


# ── Integration Tests ─────────────────────────────────────────────────────────


def test_timeout_is_greater_than_poll_interval():
    """Test that timeout is much greater than poll interval."""
    assert CI_WAIT_TIMEOUT_SECONDS > CI_POLL_INTERVAL_SECONDS * 10, (
        "Timeout should be at least 10x the poll interval"
    )


def test_timeout_allows_sufficient_polls():
    """Test that timeout allows for sufficient polling attempts."""
    max_polls = CI_WAIT_TIMEOUT_SECONDS // CI_POLL_INTERVAL_SECONDS
    assert max_polls >= 30, "Should allow at least 30 polling attempts"
    assert max_polls == 60, "With 30 min timeout and 30s interval, should allow 60 polls"


def test_ci_wait_constants_are_exported():
    """Test that key constants are available for import."""
    from tools.ci_wait import CI_WAIT_TIMEOUT_SECONDS, CI_POLL_INTERVAL_SECONDS
    
    assert isinstance(CI_WAIT_TIMEOUT_SECONDS, int)
    assert isinstance(CI_POLL_INTERVAL_SECONDS, int)
    assert CI_WAIT_TIMEOUT_SECONDS > 0
    assert CI_POLL_INTERVAL_SECONDS > 0
