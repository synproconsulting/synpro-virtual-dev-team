"""
tools/github_client.py
──────────────────────
Low-level GitHub REST API v3 wrapper.
Handles repo creation, branch management, file commits, and pull requests.
"""

import os
import base64
import time
import requests
from dotenv import load_dotenv
from typing import Optional, Dict, List

load_dotenv()

GITHUB_TOKEN    = os.environ["GITHUB_TOKEN"]
GITHUB_USERNAME = os.environ["GITHUB_USERNAME"]
GITHUB_REPO     = os.environ["GITHUB_REPO"]

# CI wait timeout configuration (in seconds)
CI_WAIT_TIMEOUT_SECONDS = 30 * 60  # 30 minutes (extended from 15 minutes)
CI_POLL_INTERVAL_SECONDS = 30  # Poll every 30 seconds

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
BASE_URL = "https://api.github.com"
REPO_URL = f"{BASE_URL}/repos/{GITHUB_USERNAME}/{GITHUB_REPO}"


def _get(path: str, params: dict = None) -> dict:
    r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params)
    if not r.ok:
        raise Exception(f"{r.status_code} {r.reason}: {r.text[:400]}")
    return r.json()


def _post(path: str, payload: dict) -> dict:
    r = requests.post(f"{BASE_URL}{path}", headers=HEADERS, json=payload)
    if not r.ok:
        raise Exception(f"{r.status_code} {r.reason}: {r.text[:400]}")
    return r.json()


def _put(path: str, payload: dict) -> dict:
    r = requests.put(f"{BASE_URL}{path}", headers=HEADERS, json=payload)
    if not r.ok:
        raise Exception(f"{r.status_code} {r.reason}: {r.text[:400]}")
    return r.json()


# ── Repository ─────────────────────────────────────────────────────────────────

def ensure_repo_exists() -> dict:
    """Create the repo if it doesn't exist. Returns repo info."""
    try:
        return _get(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}")
    except Exception:
        data = _post("/user/repos", {
            "name": GITHUB_REPO,
            "description": "Virtual Dev Team — AI-powered development",
            "private": False,
            "auto_init": True,
        })
        return data


def get_default_branch() -> str:
    """Return the default branch name (usually 'main')."""
    repo = _get(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}")
    return repo.get("default_branch", "main")


def get_branch_sha(branch: str) -> str:
    """Return the latest commit SHA for a branch."""
    data = _get(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/git/ref/heads/{branch}")
    return data["object"]["sha"]


# ── Branches ──────────────────────────────────────────────────────────────────

def create_branch(branch_name: str, from_branch: str = "main") -> dict:
    """Create a fresh branch from from_branch, deleting any existing branch with the same name."""
    try:
        _get(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/git/ref/heads/{branch_name}")
        requests.delete(
            f"{BASE_URL}/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/git/refs/heads/{branch_name}",
            headers=HEADERS,
        )
    except Exception:
        pass
    sha = get_branch_sha(from_branch)
    return _post(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/git/refs", {
        "ref": f"refs/heads/{branch_name}",
        "sha": sha,
    })


def list_branches() -> list[dict]:
    """List all branches in the repo."""
    data = _get(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/branches")
    return [{"name": b["name"]} for b in data]


# ── Files ─────────────────────────────────────────────────────────────────────

def get_file(path: str, branch: str = "main") -> Optional[dict]:
    """Get file content and SHA. Returns None if not found."""
    try:
        data = _get(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{path}",
                    params={"ref": branch})
        content = base64.b64decode(data["content"]).decode("utf-8")
        return {"content": content, "sha": data["sha"]}
    except Exception:
        return None


def commit_file(path: str, content: str, message: str,
                branch: str = "main") -> dict:
    """Create or update a file on a branch. Handles both new and existing files."""
    existing = get_file(path, branch)
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": branch,
    }
    if existing:
        payload["sha"] = existing["sha"]
    return _put(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{path}", payload)


def commit_multiple_files(files: list[dict], message: str, branch: str) -> dict:
    """
    Commit multiple files in one tree commit.
    files: list of {"path": str, "content": str}
    """
    base_sha = get_branch_sha(branch)
    base_commit = _get(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/git/commits/{base_sha}")
    base_tree_sha = base_commit["tree"]["sha"]

    tree_items = []
    for f in files:
        blob = _post(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/git/blobs", {
            "content": f["content"],
            "encoding": "utf-8",
        })
        tree_items.append({
            "path": f["path"],
            "mode": "100644",
            "type": "blob",
            "sha": blob["sha"],
        })

    new_tree = _post(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/git/trees", {
        "base_tree": base_tree_sha,
        "tree": tree_items,
    })

    new_commit = _post(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/git/commits", {
        "message": message,
        "tree": new_tree["sha"],
        "parents": [base_sha],
    })

    _put(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/git/refs/heads/{branch}", {
        "sha": new_commit["sha"],
        "force": False,
    })

    return {"commit_sha": new_commit["sha"], "branch": branch, "files": [f["path"] for f in files]}


# ── Pull Requests ─────────────────────────────────────────────────────────────

def create_pull_request(title: str, body: str,
                        head_branch: str, base_branch: str = "main") -> dict:
    """Open a pull request. Returns existing PR if one already exists for this branch."""
    existing = _get(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/pulls",
                    params={"head": f"{GITHUB_USERNAME}:{head_branch}", "state": "open"})
    if existing:
        return {"number": existing[0]["number"], "url": existing[0]["html_url"], "existing": True}

    return _post(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/pulls", {
        "title": title,
        "body": body,
        "head": head_branch,
        "base": base_branch,
    })


def list_pull_requests(state: str = "open") -> list[dict]:
    """List pull requests."""
    prs = _get(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/pulls", params={"state": state})
    return [{"number": p["number"], "title": p["title"],
             "branch": p["head"]["ref"], "url": p["html_url"]} for p in prs]


def list_tree(branch: str = "main", path_prefix: str = "") -> list[dict]:
    """Return all blob entries in the repo tree, optionally filtered by path prefix.
    Each entry: {"path": str, "sha": str, "size": int}
    """
    sha = get_branch_sha(branch)
    data = _get(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/git/trees/{sha}",
                params={"recursive": "1"})
    if data.get("truncated"):
        raise Exception("Repo tree was truncated by GitHub — repo may be too large for recursive tree fetch")
    blobs = [{"path": item["path"], "sha": item["sha"], "size": item.get("size", 0)}
             for item in data["tree"] if item["type"] == "blob"]
    if path_prefix:
        prefix = path_prefix.strip("/") + "/"
        blobs = [b for b in blobs if b["path"].startswith(prefix) or b["path"] == path_prefix.strip("/")]
    return blobs


def get_repo_url() -> str:
    return f"https://github.com/{GITHUB_USERNAME}/{GITHUB_REPO}"


# ── CI/CD Checks ──────────────────────────────────────────────────────────────

def get_commit_status(commit_sha: str) -> Dict:
    """Get the combined CI status for a commit.
    
    Args:
        commit_sha: Git commit SHA
        
    Returns:
        Dictionary with status information:
        - state: "pending", "success", "failure", or "error"
        - statuses: List of individual status checks
        - total_count: Number of status checks
    """
    data = _get(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/commits/{commit_sha}/status")
    return {
        "state": data.get("state", "pending"),
        "statuses": data.get("statuses", []),
        "total_count": data.get("total_count", 0),
    }


def get_check_runs(commit_sha: str) -> Dict:
    """Get check runs (GitHub Actions, etc.) for a commit.
    
    Args:
        commit_sha: Git commit SHA
        
    Returns:
        Dictionary with check run information:
        - total_count: Number of check runs
        - check_runs: List of check run objects
    """
    data = _get(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/commits/{commit_sha}/check-runs")
    return {
        "total_count": data.get("total_count", 0),
        "check_runs": data.get("check_runs", []),
    }


def get_combined_ci_status(commit_sha: str) -> Dict:
    """Get combined status from both status checks and check runs.
    
    Args:
        commit_sha: Git commit SHA
        
    Returns:
        Dictionary with:
        - state: Overall state ("pending", "success", "failure", "error")
        - conclusion: Overall conclusion from check runs
        - all_passed: Boolean indicating if all checks passed
        - checks: Combined list of all checks
    """
    # Get traditional status checks
    status = get_commit_status(commit_sha)
    
    # Get check runs (GitHub Actions)
    check_runs = get_check_runs(commit_sha)
    
    # Determine overall state
    all_checks = []
    
    # Process status checks
    for s in status.get("statuses", []):
        all_checks.append({
            "name": s.get("context", "Unknown"),
            "state": s.get("state", "pending"),
            "type": "status",
        })
    
    # Process check runs
    for cr in check_runs.get("check_runs", []):
        all_checks.append({
            "name": cr.get("name", "Unknown"),
            "status": cr.get("status", "queued"),
            "conclusion": cr.get("conclusion"),
            "type": "check_run",
        })
    
    # Determine overall state
    if not all_checks:
        overall_state = "pending"
        all_passed = False
    else:
        # Check if any failed
        has_failure = any(
            (c.get("state") in ["failure", "error"] if c["type"] == "status" 
             else c.get("conclusion") in ["failure", "cancelled", "timed_out"])
            for c in all_checks
        )
        
        # Check if all completed successfully
        all_success = all(
            (c.get("state") == "success" if c["type"] == "status"
             else c.get("status") == "completed" and c.get("conclusion") == "success")
            for c in all_checks
        )
        
        if has_failure:
            overall_state = "failure"
            all_passed = False
        elif all_success:
            overall_state = "success"
            all_passed = True
        else:
            overall_state = "pending"
            all_passed = False
    
    return {
        "state": overall_state,
        "all_passed": all_passed,
        "checks": all_checks,
        "total_checks": len(all_checks),
    }


def wait_for_ci_completion(
    commit_sha: str,
    timeout_seconds: int = CI_WAIT_TIMEOUT_SECONDS,
    poll_interval: int = CI_POLL_INTERVAL_SECONDS,
    verbose: bool = True,
) -> Dict:
    """Wait for CI checks to complete on a commit.
    
    Polls the commit status and check runs until all checks complete
    or the timeout is reached.
    
    Args:
        commit_sha: Git commit SHA to monitor
        timeout_seconds: Maximum time to wait in seconds (default: 30 minutes)
        poll_interval: How often to poll in seconds (default: 30 seconds)
        verbose: Whether to print status updates
        
    Returns:
        Dictionary with final CI status:
        - completed: Boolean indicating if checks completed
        - timed_out: Boolean indicating if wait timed out
        - all_passed: Boolean indicating if all checks passed
        - state: Final state
        - duration_seconds: How long the wait took
        - checks: List of all checks and their results
        
    Raises:
        Exception: If there's an error fetching CI status
    """
    start_time = time.time()
    elapsed = 0
    
    if verbose:
        print(f"[CI WAIT] Waiting for CI checks on commit {commit_sha[:8]}...")
        print(f"[CI WAIT] Timeout: {timeout_seconds / 60:.1f} minutes")
    
    while elapsed < timeout_seconds:
        try:
            status = get_combined_ci_status(commit_sha)
            
            if verbose:
                state = status["state"]
                total = status["total_checks"]
                print(f"[CI WAIT] {elapsed:.0f}s elapsed - State: {state}, Checks: {total}")
            
            # Check if all checks are complete
            if status["state"] in ["success", "failure", "error"]:
                duration = time.time() - start_time
                
                if verbose:
                    if status["all_passed"]:
                        print(f"[CI WAIT] ✓ All CI checks passed after {duration:.1f}s")
                    else:
                        print(f"[CI WAIT] ✗ CI checks failed after {duration:.1f}s")
                        for check in status["checks"]:
                            if check["type"] == "status" and check.get("state") != "success":
                                print(f"[CI WAIT]   - {check['name']}: {check['state']}")
                            elif check["type"] == "check_run" and check.get("conclusion") != "success":
                                print(f"[CI WAIT]   - {check['name']}: {check['conclusion']}")
                
                return {
                    "completed": True,
                    "timed_out": False,
                    "all_passed": status["all_passed"],
                    "state": status["state"],
                    "duration_seconds": duration,
                    "checks": status["checks"],
                }
            
            # Wait before next poll
            time.sleep(poll_interval)
            elapsed = time.time() - start_time
            
        except Exception as e:
            if verbose:
                print(f"[CI WAIT] Error checking CI status: {e}")
            raise
    
    # Timeout reached
    duration = time.time() - start_time
    final_status = get_combined_ci_status(commit_sha)
    
    if verbose:
        print(f"[CI WAIT] ⚠ Timeout reached after {duration:.1f}s")
        print(f"[CI WAIT] Final state: {final_status['state']}")
    
    return {
        "completed": False,
        "timed_out": True,
        "all_passed": False,
        "state": final_status["state"],
        "duration_seconds": duration,
        "checks": final_status["checks"],
    }


def wait_for_pr_ci(
    pr_number: int,
    timeout_seconds: int = CI_WAIT_TIMEOUT_SECONDS,
    poll_interval: int = CI_POLL_INTERVAL_SECONDS,
    verbose: bool = True,
) -> Dict:
    """Wait for CI checks to complete on a pull request.
    
    Convenience wrapper that gets the PR's head commit and waits for CI.
    
    Args:
        pr_number: Pull request number
        timeout_seconds: Maximum time to wait in seconds (default: 30 minutes)
        poll_interval: How often to poll in seconds (default: 30 seconds)
        verbose: Whether to print status updates
        
    Returns:
        Same as wait_for_ci_completion()
    """
    # Get PR details to find head commit
    pr = _get(f"/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/pulls/{pr_number}")
    head_sha = pr["head"]["sha"]
    
    if verbose:
        print(f"[CI WAIT] PR #{pr_number}: {pr['title']}")
        print(f"[CI WAIT] Head commit: {head_sha[:8]}")
    
    return wait_for_ci_completion(head_sha, timeout_seconds, poll_interval, verbose)
