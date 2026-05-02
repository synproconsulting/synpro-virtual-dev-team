"""
tools/ci_wait.py
────────────────
Wait for GitHub CI checks to complete on a pull request.

This module provides functionality to poll GitHub's check runs API
and wait for all CI checks to complete with a configurable timeout.
"""

import os
import time
from typing import Dict, List, Optional, Tuple
from enum import Enum
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_USERNAME = os.environ["GITHUB_USERNAME"]
GITHUB_REPO = os.environ["GITHUB_REPO"]

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
BASE_URL = "https://api.github.com"
REPO_URL = f"{BASE_URL}/repos/{GITHUB_USERNAME}/{GITHUB_REPO}"

# CI wait configuration
# Increased from 15 minutes to 30 minutes per SDT1-64
CI_WAIT_TIMEOUT_SECONDS = 30 * 60  # 30 minutes
CI_POLL_INTERVAL_SECONDS = 30  # Poll every 30 seconds


class CheckStatus(Enum):
    """GitHub check run status values."""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class CheckConclusion(Enum):
    """GitHub check run conclusion values."""
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"
    ACTION_REQUIRED = "action_required"


class CIWaitResult:
    """Result of waiting for CI checks."""
    
    def __init__(
        self,
        success: bool,
        timeout: bool,
        duration_seconds: float,
        check_runs: List[Dict],
        message: str,
    ):
        """
        Initialize CI wait result.
        
        Args:
            success: Whether all checks passed
            timeout: Whether the wait timed out
            duration_seconds: How long we waited
            check_runs: List of check run data
            message: Human-readable result message
        """
        self.success = success
        self.timeout = timeout
        self.duration_seconds = duration_seconds
        self.check_runs = check_runs
        self.message = message
    
    def __repr__(self) -> str:
        status = "SUCCESS" if self.success else "TIMEOUT" if self.timeout else "FAILURE"
        return f"CIWaitResult({status}, {self.duration_seconds:.1f}s, {len(self.check_runs)} checks)"


def get_pr_head_sha(pr_number: int) -> Optional[str]:
    """
    Get the HEAD SHA of a pull request.
    
    Args:
        pr_number: Pull request number
    
    Returns:
        HEAD commit SHA or None if PR not found
    """
    try:
        response = requests.get(
            f"{REPO_URL}/pulls/{pr_number}",
            headers=HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        pr_data = response.json()
        return pr_data["head"]["sha"]
    except Exception as e:
        print(f"Error getting PR #{pr_number} HEAD SHA: {e}")
        return None


def get_commit_check_runs(commit_sha: str) -> List[Dict]:
    """
    Get all check runs for a commit.
    
    Args:
        commit_sha: Git commit SHA
    
    Returns:
        List of check run dictionaries
    """
    try:
        response = requests.get(
            f"{REPO_URL}/commits/{commit_sha}/check-runs",
            headers=HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("check_runs", [])
    except Exception as e:
        print(f"Error getting check runs for {commit_sha[:8]}: {e}")
        return []


def get_commit_status(commit_sha: str) -> Dict:
    """
    Get the combined status for a commit.
    
    This checks the older "statuses" API which some CI systems still use
    in addition to the newer "check runs" API.
    
    Args:
        commit_sha: Git commit SHA
    
    Returns:
        Combined status dictionary
    """
    try:
        response = requests.get(
            f"{REPO_URL}/commits/{commit_sha}/status",
            headers=HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error getting commit status for {commit_sha[:8]}: {e}")
        return {}


def are_checks_complete(commit_sha: str) -> Tuple[bool, List[Dict], str]:
    """
    Check if all CI checks are complete for a commit.
    
    Args:
        commit_sha: Git commit SHA
    
    Returns:
        Tuple of (all_complete, check_runs, summary_message)
    """
    # Get check runs
    check_runs = get_commit_check_runs(commit_sha)
    
    # Also get commit status for older CI systems
    commit_status = get_commit_status(commit_sha)
    combined_state = commit_status.get("state", "pending")
    
    if not check_runs:
        # No check runs found, rely on commit status
        if combined_state == "pending":
            return False, [], "No check runs found, waiting for CI to start..."
        elif combined_state == "success":
            return True, [], "All status checks passed (using commit status API)"
        else:
            return True, [], f"Status checks completed with state: {combined_state}"
    
    # Check if all runs are completed
    incomplete = []
    failed = []
    passed = []
    
    for run in check_runs:
        status = run.get("status")
        conclusion = run.get("conclusion")
        name = run.get("name", "Unknown")
        
        if status != CheckStatus.COMPLETED.value:
            incomplete.append(name)
        elif conclusion == CheckConclusion.SUCCESS.value:
            passed.append(name)
        elif conclusion in [CheckConclusion.SKIPPED.value, CheckConclusion.NEUTRAL.value]:
            # Skipped and neutral are considered non-blocking
            passed.append(name)
        else:
            failed.append(name)
    
    # Build summary message
    total = len(check_runs)
    complete = total - len(incomplete)
    
    if incomplete:
        summary = f"CI in progress: {complete}/{total} checks complete. Waiting for: {', '.join(incomplete)}"
        return False, check_runs, summary
    elif failed:
        summary = f"CI completed: {len(passed)} passed, {len(failed)} failed. Failed: {', '.join(failed)}"
        return True, check_runs, summary
    else:
        summary = f"CI completed: All {total} checks passed ✓"
        return True, check_runs, summary


def wait_for_ci(
    pr_number: int,
    timeout_seconds: int = CI_WAIT_TIMEOUT_SECONDS,
    poll_interval: int = CI_POLL_INTERVAL_SECONDS,
    verbose: bool = True,
) -> CIWaitResult:
    """
    Wait for CI checks to complete on a pull request.
    
    This function polls the GitHub API until all CI checks are complete
    or the timeout is reached. The timeout has been increased from 15
    to 30 minutes to accommodate longer-running CI pipelines.
    
    Args:
        pr_number: Pull request number
        timeout_seconds: Maximum time to wait (default: 30 minutes)
        poll_interval: How often to poll in seconds (default: 30 seconds)
        verbose: Whether to print progress messages
    
    Returns:
        CIWaitResult with outcome details
    """
    start_time = time.time()
    
    if verbose:
        print(f"⏳ Waiting for CI checks on PR #{pr_number} (timeout: {timeout_seconds/60:.0f} minutes)...")
    
    # Get PR HEAD SHA
    head_sha = get_pr_head_sha(pr_number)
    if not head_sha:
        return CIWaitResult(
            success=False,
            timeout=False,
            duration_seconds=time.time() - start_time,
            check_runs=[],
            message=f"Failed to get PR #{pr_number} details",
        )
    
    if verbose:
        print(f"📍 Monitoring commit: {head_sha[:8]}")
    
    # Poll for check completion
    poll_count = 0
    last_message = ""
    
    while True:
        elapsed = time.time() - start_time
        
        # Check timeout
        if elapsed > timeout_seconds:
            message = f"⏱️  CI wait timeout after {elapsed/60:.1f} minutes"
            if verbose:
                print(message)
            
            check_runs = get_commit_check_runs(head_sha)
            return CIWaitResult(
                success=False,
                timeout=True,
                duration_seconds=elapsed,
                check_runs=check_runs,
                message=message,
            )
        
        # Check CI status
        all_complete, check_runs, summary = are_checks_complete(head_sha)
        
        # Print status update if changed
        if verbose and summary != last_message:
            print(f"  [{elapsed/60:.1f}m] {summary}")
            last_message = summary
        
        if all_complete:
            # Determine if checks passed
            success = all(
                run.get("conclusion") in [
                    CheckConclusion.SUCCESS.value,
                    CheckConclusion.SKIPPED.value,
                    CheckConclusion.NEUTRAL.value,
                    None,  # No conclusion means success for commit status API
                ]
                for run in check_runs
            )
            
            message = f"✓ CI completed in {elapsed/60:.1f} minutes: {summary}"
            if verbose:
                print(message)
            
            return CIWaitResult(
                success=success,
                timeout=False,
                duration_seconds=elapsed,
                check_runs=check_runs,
                message=message,
            )
        
        # Wait before next poll
        poll_count += 1
        time.sleep(poll_interval)


def wait_for_ci_by_branch(
    branch_name: str,
    timeout_seconds: int = CI_WAIT_TIMEOUT_SECONDS,
    poll_interval: int = CI_POLL_INTERVAL_SECONDS,
    verbose: bool = True,
) -> CIWaitResult:
    """
    Wait for CI checks on a branch by finding its open PR.
    
    Args:
        branch_name: Branch name (e.g., "feature/sdt1-64-ci-timeout")
        timeout_seconds: Maximum time to wait (default: 30 minutes)
        poll_interval: How often to poll in seconds (default: 30 seconds)
        verbose: Whether to print progress messages
    
    Returns:
        CIWaitResult with outcome details
    """
    try:
        # Find open PR for this branch
        response = requests.get(
            f"{REPO_URL}/pulls",
            headers=HEADERS,
            params={"head": f"{GITHUB_USERNAME}:{branch_name}", "state": "open"},
            timeout=10,
        )
        response.raise_for_status()
        prs = response.json()
        
        if not prs:
            return CIWaitResult(
                success=False,
                timeout=False,
                duration_seconds=0,
                check_runs=[],
                message=f"No open PR found for branch '{branch_name}'",
            )
        
        pr_number = prs[0]["number"]
        return wait_for_ci(pr_number, timeout_seconds, poll_interval, verbose)
    
    except Exception as e:
        return CIWaitResult(
            success=False,
            timeout=False,
            duration_seconds=0,
            check_runs=[],
            message=f"Error finding PR for branch '{branch_name}': {e}",
        )


def get_ci_summary(pr_number: int) -> str:
    """
    Get a human-readable summary of CI status for a PR.
    
    Args:
        pr_number: Pull request number
    
    Returns:
        Formatted CI status summary
    """
    head_sha = get_pr_head_sha(pr_number)
    if not head_sha:
        return f"Could not get PR #{pr_number} details"
    
    _, check_runs, summary = are_checks_complete(head_sha)
    
    if not check_runs:
        commit_status = get_commit_status(head_sha)
        state = commit_status.get("state", "unknown")
        return f"PR #{pr_number}: No check runs, commit status = {state}"
    
    lines = [f"PR #{pr_number} CI Status:", ""]
    for run in check_runs:
        name = run.get("name", "Unknown")
        status = run.get("status", "unknown")
        conclusion = run.get("conclusion", "-")
        
        if status == CheckStatus.COMPLETED.value:
            icon = "✓" if conclusion == CheckConclusion.SUCCESS.value else "✗"
            lines.append(f"  {icon} {name}: {conclusion}")
        else:
            lines.append(f"  ⏳ {name}: {status}")
    
    lines.append("")
    lines.append(summary)
    
    return "\n".join(lines)


# ── Configuration Constants ───────────────────────────────────────────────────

# Export timeout constant for use by other modules
__all__ = [
    "CI_WAIT_TIMEOUT_SECONDS",
    "CI_POLL_INTERVAL_SECONDS",
    "wait_for_ci",
    "wait_for_ci_by_branch",
    "get_ci_summary",
    "CIWaitResult",
    "CheckStatus",
    "CheckConclusion",
]
