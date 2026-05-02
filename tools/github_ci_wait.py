"""
tools/github_ci_wait.py
───────────────────────
Utilities for waiting on GitHub Actions CI workflow completion.

This module provides functionality to poll GitHub Actions workflow runs
and wait for them to complete successfully before proceeding with ticket execution.
"""

import os
import time
import requests
from typing import Optional, Dict, List
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

# CI wait timeout extended from 15 to 30 minutes (SDT1-64)
DEFAULT_CI_TIMEOUT_SECONDS = 30 * 60  # 30 minutes
DEFAULT_POLL_INTERVAL_SECONDS = 30  # Poll every 30 seconds


def _get(path: str, params: dict = None) -> dict:
    """Make a GET request to GitHub API.
    
    Args:
        path: API endpoint path
        params: Optional query parameters
        
    Returns:
        JSON response dictionary
        
    Raises:
        Exception: If request fails
    """
    r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params)
    if not r.ok:
        raise Exception(f"{r.status_code} {r.reason}: {r.text[:400]}")
    return r.json()


def get_latest_workflow_run(branch: str, workflow_name: Optional[str] = None) -> Optional[Dict]:
    """Get the latest workflow run for a branch.
    
    Args:
        branch: Branch name
        workflow_name: Optional workflow filename (e.g., 'ci.yml')
        
    Returns:
        Workflow run dictionary or None if no runs found
    """
    params = {
        "branch": branch,
        "per_page": 1,
    }
    
    endpoint = f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/actions/runs"
    
    data = _get(endpoint, params=params)
    runs = data.get("workflow_runs", [])
    
    if not runs:
        return None
    
    # If workflow_name is specified, filter by it
    if workflow_name:
        for run in runs:
            if run.get("path", "").endswith(workflow_name):
                return run
        return None
    
    return runs[0]


def get_workflow_run_status(run_id: int) -> Dict:
    """Get the status of a workflow run.
    
    Args:
        run_id: Workflow run ID
        
    Returns:
        Dictionary with 'status' and 'conclusion' keys
        - status: 'queued', 'in_progress', 'completed'
        - conclusion: 'success', 'failure', 'cancelled', 'skipped', None if not completed
    """
    endpoint = f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/actions/runs/{run_id}"
    data = _get(endpoint)
    
    return {
        "status": data.get("status"),
        "conclusion": data.get("conclusion"),
        "html_url": data.get("html_url"),
        "id": data.get("id"),
        "name": data.get("name"),
    }


def wait_for_ci_completion(
    branch: str,
    timeout_seconds: int = DEFAULT_CI_TIMEOUT_SECONDS,
    poll_interval: int = DEFAULT_POLL_INTERVAL_SECONDS,
    workflow_name: Optional[str] = None,
    verbose: bool = True,
) -> Dict:
    """Wait for CI workflow to complete on a branch.
    
    Args:
        branch: Branch name to monitor
        timeout_seconds: Maximum time to wait in seconds (default: 1800 = 30 minutes)
        poll_interval: Time between status checks in seconds (default: 30)
        workflow_name: Optional workflow filename to monitor (default: any workflow)
        verbose: Whether to print status updates
        
    Returns:
        Dictionary with final workflow status:
        {
            'success': bool,
            'status': str,
            'conclusion': str,
            'timed_out': bool,
            'html_url': str,
            'elapsed_seconds': float
        }
        
    Examples:
        >>> result = wait_for_ci_completion("feature/my-branch")
        >>> if result['success']:
        ...     print("CI passed!")
        ... else:
        ...     print(f"CI failed: {result['conclusion']}")
    """
    if verbose:
        print(f"[CI-WAIT] Waiting for CI on branch '{branch}' (timeout: {timeout_seconds}s)")
    
    start_time = time.time()
    elapsed = 0.0
    
    # Give GitHub a moment to register the push and start the workflow
    time.sleep(5)
    
    while elapsed < timeout_seconds:
        try:
            # Get latest workflow run
            run = get_latest_workflow_run(branch, workflow_name)
            
            if not run:
                if verbose:
                    print(f"[CI-WAIT] No workflow runs found for branch '{branch}' yet...")
                time.sleep(poll_interval)
                elapsed = time.time() - start_time
                continue
            
            run_id = run.get("id")
            status_info = get_workflow_run_status(run_id)
            
            status = status_info.get("status")
            conclusion = status_info.get("conclusion")
            
            if verbose:
                print(f"[CI-WAIT] Workflow #{run_id} status: {status}, conclusion: {conclusion}")
            
            # Check if workflow is complete
            if status == "completed":
                elapsed = time.time() - start_time
                
                success = conclusion == "success"
                
                if verbose:
                    if success:
                        print(f"[CI-WAIT] ✓ CI passed after {elapsed:.1f}s")
                    else:
                        print(f"[CI-WAIT] ✗ CI {conclusion} after {elapsed:.1f}s")
                        print(f"[CI-WAIT] Workflow URL: {status_info.get('html_url')}")
                
                return {
                    "success": success,
                    "status": status,
                    "conclusion": conclusion,
                    "timed_out": False,
                    "html_url": status_info.get("html_url"),
                    "elapsed_seconds": elapsed,
                    "run_id": run_id,
                }
            
            # Workflow still running, continue polling
            time.sleep(poll_interval)
            elapsed = time.time() - start_time
            
        except Exception as e:
            if verbose:
                print(f"[CI-WAIT] Error checking workflow status: {e}")
            time.sleep(poll_interval)
            elapsed = time.time() - start_time
    
    # Timeout reached
    elapsed = time.time() - start_time
    
    if verbose:
        print(f"[CI-WAIT] ⏱  Timeout reached after {elapsed:.1f}s")
    
    return {
        "success": False,
        "status": "timeout",
        "conclusion": "timeout",
        "timed_out": True,
        "html_url": None,
        "elapsed_seconds": elapsed,
        "run_id": None,
    }


def wait_for_pr_ci(
    pr_number: int,
    timeout_seconds: int = DEFAULT_CI_TIMEOUT_SECONDS,
    poll_interval: int = DEFAULT_POLL_INTERVAL_SECONDS,
    verbose: bool = True,
) -> Dict:
    """Wait for CI checks to complete on a pull request.
    
    Args:
        pr_number: Pull request number
        timeout_seconds: Maximum time to wait in seconds (default: 1800 = 30 minutes)
        poll_interval: Time between status checks in seconds (default: 30)
        verbose: Whether to print status updates
        
    Returns:
        Dictionary with CI check results
        
    Examples:
        >>> result = wait_for_pr_ci(42)
        >>> if result['success']:
        ...     print("All PR checks passed!")
    """
    if verbose:
        print(f"[CI-WAIT] Waiting for CI checks on PR #{pr_number} (timeout: {timeout_seconds}s)")
    
    # Get PR details to find the head branch
    endpoint = f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/pulls/{pr_number}"
    pr_data = _get(endpoint)
    
    head_branch = pr_data.get("head", {}).get("ref")
    
    if not head_branch:
        return {
            "success": False,
            "status": "error",
            "conclusion": "Could not determine head branch",
            "timed_out": False,
            "html_url": None,
            "elapsed_seconds": 0.0,
        }
    
    # Wait for CI on the head branch
    return wait_for_ci_completion(
        branch=head_branch,
        timeout_seconds=timeout_seconds,
        poll_interval=poll_interval,
        verbose=verbose,
    )


def get_ci_timeout_seconds() -> int:
    """Get CI wait timeout from environment variable or use default.
    
    Environment variable:
        CI_WAIT_TIMEOUT_SECONDS: Override default timeout (default: 1800 = 30 minutes)
        
    Returns:
        Timeout in seconds
    """
    timeout_str = os.environ.get("CI_WAIT_TIMEOUT_SECONDS", str(DEFAULT_CI_TIMEOUT_SECONDS))
    
    try:
        timeout = int(timeout_str)
        if timeout <= 0:
            print(f"[CI-WAIT] Warning: Invalid timeout {timeout}, using default {DEFAULT_CI_TIMEOUT_SECONDS}s")
            return DEFAULT_CI_TIMEOUT_SECONDS
        return timeout
    except ValueError:
        print(f"[CI-WAIT] Warning: Invalid timeout value '{timeout_str}', using default {DEFAULT_CI_TIMEOUT_SECONDS}s")
        return DEFAULT_CI_TIMEOUT_SECONDS
