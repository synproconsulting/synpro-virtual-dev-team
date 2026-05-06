"""
agents/orchestrator_ci_monitor.py
──────────────────────────────────
CI/CD monitoring module for the Orchestrator.

This module provides functionality to monitor GitHub Actions CI/CD pipeline
status when the Orchestrator executes tickets that trigger deployments.

The monitor waits for CI pipelines to complete with a configurable timeout.
"""

import os
import time
from typing import Optional, Dict, Literal
from datetime import datetime, timedelta

import requests


# CI wait timeout extended from 15 to 30 minutes (SDT1-64)
CI_WAIT_TIMEOUT_MINUTES = 30
CI_POLL_INTERVAL_SECONDS = 30


class CITimeoutError(Exception):
    """Exception raised when CI pipeline exceeds wait timeout."""
    pass


class CIMonitor:
    """Monitor GitHub Actions CI/CD pipeline status."""
    
    def __init__(
        self,
        github_token: Optional[str] = None,
        timeout_minutes: int = CI_WAIT_TIMEOUT_MINUTES,
        poll_interval_seconds: int = CI_POLL_INTERVAL_SECONDS,
        verbose: bool = True,
    ):
        """Initialize CI monitor.
        
        Args:
            github_token: GitHub token for API access. If None, reads from GITHUB_TOKEN env var.
            timeout_minutes: Maximum time to wait for CI completion (default: 30 minutes)
            poll_interval_seconds: Interval between status checks (default: 30 seconds)
            verbose: Whether to print status updates
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.timeout_minutes = timeout_minutes
        self.poll_interval_seconds = poll_interval_seconds
        self.verbose = verbose
        
        if not self.github_token:
            raise ValueError("GitHub token required. Set GITHUB_TOKEN env var or pass github_token parameter.")
    
    def log(self, message: str) -> None:
        """Log a message if verbose mode is enabled.
        
        Args:
            message: Message to log
        """
        if self.verbose:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            print(f"[CI-MONITOR {timestamp}] {message}")
    
    def get_workflow_runs(
        self,
        repo_owner: str,
        repo_name: str,
        branch: str,
        commit_sha: Optional[str] = None,
    ) -> list:
        """Get workflow runs for a repository branch.
        
        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            branch: Branch name
            commit_sha: Optional commit SHA to filter by
            
        Returns:
            List of workflow run dictionaries
        """
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs"
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        
        params = {
            "branch": branch,
            "per_page": 10,
        }
        
        if commit_sha:
            params["head_sha"] = commit_sha
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data.get("workflow_runs", [])
    
    def get_workflow_run_status(
        self,
        repo_owner: str,
        repo_name: str,
        run_id: int,
    ) -> Dict:
        """Get detailed status of a workflow run.
        
        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            run_id: Workflow run ID
            
        Returns:
            Dictionary with status, conclusion, and other details
        """
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs/{run_id}"
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        return {
            "id": data["id"],
            "status": data["status"],  # queued, in_progress, completed
            "conclusion": data.get("conclusion"),  # success, failure, cancelled, skipped, etc.
            "html_url": data["html_url"],
            "created_at": data["created_at"],
            "updated_at": data["updated_at"],
        }
    
    def wait_for_ci(
        self,
        repo_owner: str,
        repo_name: str,
        branch: str,
        commit_sha: Optional[str] = None,
        run_id: Optional[int] = None,
    ) -> Literal["success", "failure", "cancelled"]:
        """Wait for CI pipeline to complete.
        
        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            branch: Branch name
            commit_sha: Optional commit SHA to monitor
            run_id: Optional specific workflow run ID to monitor
            
        Returns:
            CI conclusion: "success", "failure", or "cancelled"
            
        Raises:
            CITimeoutError: If CI doesn't complete within timeout
            requests.HTTPError: If GitHub API calls fail
        """
        start_time = datetime.utcnow()
        timeout_delta = timedelta(minutes=self.timeout_minutes)
        
        self.log(
            f"Monitoring CI for {repo_owner}/{repo_name} branch '{branch}' "
            f"(timeout: {self.timeout_minutes} minutes)"
        )
        
        # If run_id not provided, find the latest run
        if not run_id:
            self.log("Finding latest workflow run...")
            runs = self.get_workflow_runs(repo_owner, repo_name, branch, commit_sha)
            
            if not runs:
                raise ValueError(f"No workflow runs found for branch '{branch}'")
            
            run_id = runs[0]["id"]
            self.log(f"Monitoring workflow run ID: {run_id}")
        
        # Poll until completion or timeout
        iteration = 0
        while True:
            iteration += 1
            elapsed = datetime.utcnow() - start_time
            
            # Check timeout
            if elapsed > timeout_delta:
                raise CITimeoutError(
                    f"CI pipeline exceeded timeout of {self.timeout_minutes} minutes. "
                    f"Run ID: {run_id}"
                )
            
            # Get current status
            try:
                status_info = self.get_workflow_run_status(repo_owner, repo_name, run_id)
            except requests.HTTPError as e:
                self.log(f"Error fetching workflow status: {e}")
                time.sleep(self.poll_interval_seconds)
                continue
            
            status = status_info["status"]
            conclusion = status_info.get("conclusion")
            
            # Log status update every 5 iterations or when status changes
            if iteration % 5 == 1:
                elapsed_str = str(elapsed).split(".")[0]  # Remove microseconds
                self.log(
                    f"Status: {status}, Conclusion: {conclusion or 'N/A'}, "
                    f"Elapsed: {elapsed_str}, URL: {status_info['html_url']}"
                )
            
            # Check if completed
            if status == "completed":
                self.log(f"CI pipeline completed with conclusion: {conclusion}")
                
                if conclusion == "success":
                    return "success"
                elif conclusion == "cancelled":
                    return "cancelled"
                else:
                    # Any other conclusion (failure, skipped, etc.) treated as failure
                    return "failure"
            
            # Wait before next poll
            time.sleep(self.poll_interval_seconds)
    
    def wait_for_ci_with_retry(
        self,
        repo_owner: str,
        repo_name: str,
        branch: str,
        commit_sha: Optional[str] = None,
        run_id: Optional[int] = None,
        max_retries: int = 3,
    ) -> Literal["success", "failure", "cancelled", "timeout"]:
        """Wait for CI pipeline with retry logic for transient errors.
        
        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            branch: Branch name
            commit_sha: Optional commit SHA to monitor
            run_id: Optional specific workflow run ID to monitor
            max_retries: Maximum number of retries for transient errors
            
        Returns:
            CI conclusion: "success", "failure", "cancelled", or "timeout"
        """
        for attempt in range(max_retries):
            try:
                return self.wait_for_ci(
                    repo_owner=repo_owner,
                    repo_name=repo_name,
                    branch=branch,
                    commit_sha=commit_sha,
                    run_id=run_id,
                )
            except CITimeoutError as e:
                self.log(f"CI timeout: {e}")
                return "timeout"
            except requests.HTTPError as e:
                if attempt < max_retries - 1:
                    self.log(f"Transient error (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(60)  # Wait 1 minute before retry
                    continue
                else:
                    self.log(f"Max retries exceeded. Last error: {e}")
                    raise
        
        return "failure"


def wait_for_ci_completion(
    repo_owner: str,
    repo_name: str,
    branch: str,
    commit_sha: Optional[str] = None,
    run_id: Optional[int] = None,
    timeout_minutes: int = CI_WAIT_TIMEOUT_MINUTES,
    github_token: Optional[str] = None,
    verbose: bool = True,
) -> Literal["success", "failure", "cancelled", "timeout"]:
    """Convenience function to wait for CI completion.
    
    Args:
        repo_owner: GitHub repository owner
        repo_name: GitHub repository name
        branch: Branch name
        commit_sha: Optional commit SHA to monitor
        run_id: Optional specific workflow run ID to monitor
        timeout_minutes: Maximum time to wait (default: 30 minutes)
        github_token: Optional GitHub token (uses GITHUB_TOKEN env var if None)
        verbose: Whether to print status updates
        
    Returns:
        CI conclusion: "success", "failure", "cancelled", or "timeout"
    """
    monitor = CIMonitor(
        github_token=github_token,
        timeout_minutes=timeout_minutes,
        verbose=verbose,
    )
    
    return monitor.wait_for_ci_with_retry(
        repo_owner=repo_owner,
        repo_name=repo_name,
        branch=branch,
        commit_sha=commit_sha,
        run_id=run_id,
    )
