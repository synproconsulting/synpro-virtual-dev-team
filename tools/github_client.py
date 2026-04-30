"""
tools/github_client.py
──────────────────────
Low-level GitHub REST API v3 wrapper.
Handles repo creation, branch management, file commits, and pull requests.
"""

import os
import base64
import requests
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

GITHUB_TOKEN    = os.environ["GITHUB_TOKEN"]
GITHUB_USERNAME = os.environ["GITHUB_USERNAME"]
GITHUB_REPO     = os.environ["GITHUB_REPO"]

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
