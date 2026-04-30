"""
ci_dev_agent.py
────────────────
Self-contained Dev Agent for GitHub Actions.
Uses a proper SDK tool-use loop: Claude reads existing files, stages changes,
then all staged files are committed in a single clean commit and a PR is opened.

Usage:
    python ci_dev_agent.py --ticket SDT1-13 --summary "Delete user account"
    python ci_dev_agent.py --ticket SDT1-13 --summary "Delete user account" --feedback "..."
"""

import os
import sys
import re
import base64
import argparse
import requests
import anthropic
from dotenv import load_dotenv

load_dotenv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Config ─────────────────────────────────────────────────────────────────────

ANTHROPIC_KEY   = os.environ["ANTHROPIC_API_KEY"]
GITHUB_TOKEN    = os.environ["GITHUB_TOKEN"]
GITHUB_USERNAME = os.environ["GITHUB_USERNAME"]
GITHUB_REPO     = os.environ["GITHUB_REPO"]

GH_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
BASE = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}"


# ── GitHub helpers ─────────────────────────────────────────────────────────────

def get_branch_sha(branch):
    r = requests.get(f"{BASE}/git/ref/heads/{branch}", headers=GH_HEADERS)
    if not r.ok:
        return None
    return r.json()["object"]["sha"]

def gh_create_branch(branch_name, from_branch="main"):
    sha = get_branch_sha(from_branch)
    if not sha:
        return False, f"Could not get SHA for {from_branch}"
    existing = get_branch_sha(branch_name)
    if existing:
        print(f"Branch {branch_name} exists — deleting and recreating from latest main")
        requests.delete(f"{BASE}/git/refs/heads/{branch_name}", headers=GH_HEADERS)
    r = requests.post(f"{BASE}/git/refs", headers=GH_HEADERS, json={
        "ref": f"refs/heads/{branch_name}",
        "sha": sha,
    })
    return r.status_code == 201, branch_name

def gh_read_file(path, branch="main"):
    r = requests.get(f"{BASE}/contents/{path}", headers=GH_HEADERS, params={"ref": branch})
    if not r.ok:
        return None
    data = r.json()
    if isinstance(data, list):  # GitHub returns a list when path is a directory, not a file
        return None
    return base64.b64decode(data["content"]).decode("utf-8")

def gh_commit_files(files, message, branch):
    """Commit multiple files in a single tree commit."""
    base_sha = get_branch_sha(branch)
    if not base_sha:
        return False, "Branch not found"

    r = requests.get(f"{BASE}/git/commits/{base_sha}", headers=GH_HEADERS)
    if not r.ok:
        return False, "Could not get base commit"
    base_tree_sha = r.json()["tree"]["sha"]

    tree_items = []
    for f in files:
        blob_r = requests.post(f"{BASE}/git/blobs", headers=GH_HEADERS,
                               json={"content": f["content"], "encoding": "utf-8"})
        if not blob_r.ok:
            return False, f"Failed to create blob for {f['path']}"
        tree_items.append({
            "path": f["path"],
            "mode": "100644",
            "type": "blob",
            "sha": blob_r.json()["sha"],
        })

    tree_r = requests.post(f"{BASE}/git/trees", headers=GH_HEADERS,
                           json={"base_tree": base_tree_sha, "tree": tree_items})
    if not tree_r.ok:
        return False, f"Failed to create tree: {tree_r.text[:200]}"

    commit_r = requests.post(f"{BASE}/git/commits", headers=GH_HEADERS,
                             json={"message": message, "tree": tree_r.json()["sha"],
                                   "parents": [base_sha]})
    if not commit_r.ok:
        return False, f"Failed to create commit: {commit_r.text[:200]}"

    ref_r = requests.patch(f"{BASE}/git/refs/heads/{branch}", headers=GH_HEADERS,
                           json={"sha": commit_r.json()["sha"], "force": False})
    if not ref_r.ok:
        return False, f"Failed to update branch ref: {ref_r.text[:200]}"

    return True, commit_r.json()["sha"]

def gh_create_pr(title, body, head_branch, base_branch="main"):
    existing = requests.get(f"{BASE}/pulls", headers=GH_HEADERS,
                            params={"head": f"{GITHUB_USERNAME}:{head_branch}", "state": "open"})
    if existing.ok and existing.json():
        pr = existing.json()[0]
        return pr["number"], pr["html_url"]
    r = requests.post(f"{BASE}/pulls", headers=GH_HEADERS,
                      json={"title": title, "body": body,
                            "head": head_branch, "base": base_branch})
    if r.ok:
        return r.json()["number"], r.json()["html_url"]
    return None, None


# ── Tool definitions ──────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "create_branch",
        "description": (
            "Create the feature branch from latest main, deleting any existing branch "
            "with the same name. Call this first, before reading or staging any files."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "branch_name": {
                    "type": "string",
                    "description": "Branch name e.g. feature/sdt1-13-delete-account",
                },
            },
            "required": ["branch_name"],
        },
    },
    {
        "name": "read_file",
        "description": (
            "Read the current content of a file from the repository. "
            "Always call this before staging any file that may already exist — "
            "you must merge your changes into the existing content, never overwrite."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path":   {"type": "string", "description": "File path relative to repo root"},
                "branch": {"type": "string", "description": "Branch to read from (default: main)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "stage_file",
        "description": (
            "Stage a file for the commit. All staged files are committed together "
            "in one clean commit when you call create_pr. "
            "For files that already exist, call read_file first and merge your changes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path":    {"type": "string", "description": "File path relative to repo root"},
                "content": {"type": "string", "description": "Complete file content"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "create_pr",
        "description": (
            "Commit all staged files in a single clean commit and open a pull request. "
            "Call this only after staging all files. "
            "PR title format: [TICKET-ID] Brief description"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "PR title e.g. [SDT1-13] Delete user account"},
                "body":  {"type": "string", "description": "PR body — what was implemented, how to test"},
            },
            "required": ["title", "body"],
        },
    },
]


# ── Tool executor ─────────────────────────────────────────────────────────────

def execute_tool(name, inputs, state):
    """Execute a tool call. state carries branch and staged files across calls."""
    if name == "create_branch":
        branch_name = inputs["branch_name"]
        ok, result = gh_create_branch(branch_name)
        if ok:
            state["branch"] = branch_name
            print(f"  create_branch: {branch_name}")
            return f"Branch '{branch_name}' created from latest main."
        print(f"  create_branch FAILED: {result}")
        return f"ERROR: {result}"

    elif name == "read_file":
        path   = inputs["path"]
        branch = inputs.get("branch", "main")
        content = gh_read_file(path, branch)
        if content is None:
            print(f"  read_file: {path} (not found on {branch})")
            return f"File '{path}' does not exist on branch '{branch}'."
        print(f"  read_file: {path} ({len(content)} chars from {branch})")
        return content

    elif name == "stage_file":
        path    = inputs["path"]
        content = inputs["content"]
        state["staged"][path] = content
        print(f"  stage_file: {path} ({len(content)} chars) — total staged: {len(state['staged'])}")
        return f"File '{path}' staged. Total staged: {len(state['staged'])}."

    elif name == "create_pr":
        branch = state.get("branch")
        staged = state.get("staged", {})
        if not branch:
            return "ERROR: No branch created yet. Call create_branch first."
        if not staged:
            return "ERROR: No files staged. Call stage_file for each file first."

        files = [{"path": p, "content": c} for p, c in staged.items()]
        ticket  = state.get("ticket", "unknown")
        summary = state.get("summary", "")
        commit_msg = f"feat({ticket.lower()}): {summary[:60].lower()}"

        print(f"\nCommitting {len(files)} file(s) to {branch}...")
        ok, result = gh_commit_files(files, commit_msg, branch)
        if not ok:
            return f"ERROR: Commit failed — {result}"
        print(f"  committed sha: {str(result)[:8]}")
        for f in files:
            print(f"    {f['path']}")

        pr_num, pr_url = gh_create_pr(inputs["title"], inputs["body"], branch)
        if pr_num:
            state["pr_number"] = pr_num
            state["pr_url"]    = pr_url
            print(f"  PR #{pr_num} opened: {pr_url}")
            return f"PR #{pr_num} opened: {pr_url}"
        return "ERROR: PR creation failed."

    return f"ERROR: Unknown tool '{name}'"


# ── Main implementation loop ──────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a skilled Python/React developer implementing Jira tickets.

Workflow (follow this exact order):
1. Call create_branch with the feature branch name
2. For every file you intend to modify or extend, call read_file first
3. Call stage_file for each new or modified file (with complete file content)
4. Call create_pr to commit everything atomically and open the PR

Repository layout rules:
- uat/backend/ is FLAT: all Python files directly in uat/backend/, no src/ subdirectory,
  no __init__.py files. Tests in uat/backend/tests/. Flat imports: from models import ...
- control-centre/src/components/ for React components; control-centre/src/api/ for API helpers
- Root-level agents/, tools/ for agent/orchestration code

Jira custom fields (when writing code that reads or writes Jira issues):
- customfield_10071 = execution_order (integer) — set on every story by PM Agent, read by Orchestrator for ticket sequencing
- customfield_10016 = story_points (integer)

Code standards:
- Python 3.11+, type hints on all functions, docstrings on all public functions/classes
- No hardcoded secrets — environment variables only
- Write meaningful pytest tests for all new backend logic
- Keep files focused; split across multiple files rather than one large file

Merge rule: If read_file returns content, you MUST incorporate the existing content
into your staged version — never discard existing code when extending a file.

Dependency rule: requirements.txt is a critical file — always read its existing content
before writing, never remove existing dependencies, only append new ones. Removing a
dependency will break the deployed service for every feature that depends on it.

PR title format: [TICKET-ID] Brief description
"""


def implement_ticket(ticket: str, summary: str, feedback: str = ""):
    print(f"\n=== CI Dev Agent [{ticket}]: {summary} ===\n")

    slug        = re.sub(r'[^a-z0-9-]', '-', summary.lower())[:40].rstrip('-')
    branch_name = f"feature/{ticket.lower()}-{slug}"

    feedback_section = (
        f"\n\nFEEDBACK FROM PREVIOUS ATTEMPT (address all points):\n{feedback}"
        if feedback else ""
    )

    user_message = (
        f"Implement this Jira ticket: [{ticket}] {summary}{feedback_section}\n\n"
        f"Suggested branch name: {branch_name}"
    )

    client   = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    messages = [{"role": "user", "content": user_message}]
    state    = {"ticket": ticket, "summary": summary, "branch": None, "staged": {}}

    print("Starting tool-use loop...\n")
    for iteration in range(40):
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"Claude: {block.text[:400]}")

        if response.stop_reason == "end_turn":
            print(f"\nAgent finished after {iteration + 1} iteration(s).")
            break

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if not tool_uses:
            print("No tool calls and stop_reason != end_turn — stopping.")
            break

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for tu in tool_uses:
            print(f"\n-> {tu.name}({list(tu.input.keys())})")
            result = execute_tool(tu.name, tu.input, state)
            tool_results.append({
                "type":        "tool_result",
                "tool_use_id": tu.id,
                "content":     result,
            })

        messages.append({"role": "user", "content": tool_results})

    pr_num = state.get("pr_number")
    pr_url = state.get("pr_url")
    staged = state.get("staged", {})

    if pr_num:
        print(f"\nDone! PR #{pr_num}: {pr_url}")
        print(f"Files: {', '.join(staged.keys())}")
    else:
        print("\nImplementation did not produce a PR.")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticket",   required=True)
    parser.add_argument("--summary",  required=True)
    parser.add_argument("--feedback", default="")
    args = parser.parse_args()
    implement_ticket(args.ticket, args.summary, args.feedback)
