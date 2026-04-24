"""
ci_dev_agent.py
────────────────
Self-contained Dev Agent for GitHub Actions.
Implements a Jira ticket by writing code, committing to a branch, and opening a PR.
Reads existing shared files before writing to avoid replacing them.

Usage:
    python ci_dev_agent.py --ticket SDT1-13 --summary "Delete user account"
    python ci_dev_agent.py --ticket SDT1-13 --summary "Delete user account" --feedback "Do not replace README"
"""

import os
import sys
import re
import base64
import argparse
import requests
import anthropic

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

def get_default_branch():
    r = requests.get(BASE, headers=GH_HEADERS)
    return r.json().get("default_branch", "main")

def get_branch_sha(branch):
    r = requests.get(f"{BASE}/git/ref/heads/{branch}", headers=GH_HEADERS)
    if not r.ok:
        return None
    return r.json()["object"]["sha"]

def create_branch(branch_name, from_branch="main"):
    sha = get_branch_sha(from_branch)
    if not sha:
        print(f"Could not get SHA for {from_branch}")
        return False
    # Check if branch exists
    existing = get_branch_sha(branch_name)
    if existing:
        print(f"Branch {branch_name} already exists")
        return True
    r = requests.post(f"{BASE}/git/refs", headers=GH_HEADERS, json={
        "ref": f"refs/heads/{branch_name}",
        "sha": sha,
    })
    return r.status_code == 201

def get_file_content(path, branch="main"):
    r = requests.get(f"{BASE}/contents/{path}",
                     headers=GH_HEADERS, params={"ref": branch})
    if not r.ok:
        return None, None
    data = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]

def commit_file(path, content, message, branch):
    existing_content, sha = get_file_content(path, branch)
    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    payload = {"message": message, "content": encoded, "branch": branch}
    if sha:
        payload["sha"] = sha
    r = requests.put(f"{BASE}/contents/{path}", headers=GH_HEADERS, json=payload)
    return r.status_code in (200, 201)

def create_pr(title, body, head_branch, base_branch="main"):
    # Check for existing PR
    existing = requests.get(f"{BASE}/pulls", headers=GH_HEADERS,
                            params={"head": f"{GITHUB_USERNAME}:{head_branch}", "state": "open"})
    if existing.ok and existing.json():
        pr = existing.json()[0]
        return pr["number"], pr["html_url"]
    r = requests.post(f"{BASE}/pulls", headers=GH_HEADERS, json={
        "title": title, "body": body,
        "head": head_branch, "base": base_branch,
    })
    if r.ok:
        return r.json()["number"], r.json()["html_url"]
    return None, None


# ── Main implementation logic ──────────────────────────────────────────────────

def implement_ticket(ticket: str, summary: str, feedback: str = ""):
    print(f"\n=== CI Dev Agent implementing [{ticket}]: {summary} ===\n")

    # Make branch name
    slug = re.sub(r'[^a-z0-9-]', '-', summary.lower())[:40].rstrip('-')
    branch = f"feature/{ticket.lower()}-{slug}"
    print(f"Branch: {branch}")

    # Read existing shared files from main
    existing_readme, _ = get_file_content("README.md", "main")
    existing_reqs, _   = get_file_content("requirements.txt", "main")
    existing_init, _   = get_file_content("src/auth/__init__.py", "main")
    existing_test_init, _ = get_file_content("tests/__init__.py", "main")

    print(f"Existing README: {'found' if existing_readme else 'not found'}")
    print(f"Existing requirements.txt: {'found' if existing_reqs else 'not found'}")

    # Ask Claude to generate the implementation
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

    feedback_section = f"\n\nFEEDBACK FROM PREVIOUS ATTEMPT (must address these):\n{feedback}" if feedback else ""

    prompt = (
        "You are a Python backend developer implementing a Jira ticket.\n\n"
        "Ticket: [" + ticket + "] " + summary + feedback_section + "\n\n"
        "RULES:\n"
        "1. Create ONLY NEW source files (e.g. src/auth/delete_account.py)\n"
        "2. Create ONLY NEW test files (e.g. tests/test_delete_account.py)\n"
        "3. Do NOT include README.md, requirements.txt, or __init__.py\n"
        "   These will be handled separately\n"
        "4. Use Python 3.11+, type hints, docstrings, pytest tests\n"
        "5. No hardcoded secrets\n\n"
        "Also provide:\n"
        "- readme_section: new markdown section to append to README\n"
        "- new_requirements: list of NEW pip packages needed\n"
        "- new_exports: list of new symbols to add to src/auth/__init__.py\n\n"
        "Respond with ONLY a JSON object:\n"
        "{\n"
        '  \"files\": [\n'
        '    {\"path\": \"src/auth/feature.py\", \"content\": \"# implementation\"},\n'
        '    {\"path\": \"tests/test_feature.py\", \"content\": \"# tests\"}\n'
        "  ],\n"
        '  \"readme_section\": \"## Feature\\n\\ndescription\",\n'
        '  \"new_requirements\": [\"package==1.0\"],\n'
        '  \"new_exports\": [\"ClassName\"],\n'
        '  \"pr_body\": \"what was implemented\"\n'
        "}"
    )

    print("\nAsking Claude to implement the ticket...")
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:-1])

    import json
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Could not parse Claude response: {e}")
        print(f"Raw: {raw[:300]}")
        sys.exit(1)

    files            = result.get("files", [])
    pr_body          = result.get("pr_body", "Implements " + summary)
    readme_section   = result.get("readme_section", "")
    new_requirements = result.get("new_requirements", [])
    new_exports      = result.get("new_exports", [])
    print(f"\nClaude generated {len(files)} new files")

    # Create branch
    print(f"\nCreating branch {branch}...")
    if not create_branch(branch):
        print("Failed to create branch")
        sys.exit(1)

    commit_msg = "feat(" + ticket.lower() + "): implement " + summary.lower()[:50]

    # Commit each NEW file
    print("\nCommitting new files...")
    committed = []
    for f in files:
        path     = f.get("path", "")
        fcontent = f.get("content", "")
        if not path or not fcontent:
            continue
        ok = commit_file(path, fcontent, commit_msg, branch)
        if ok:
            print(f"  ✓ {path}")
            committed.append(path)
        else:
            print(f"  ✗ {path} — commit failed")

    # Append to README.md
    if readme_section and existing_readme:
        new_readme = existing_readme.rstrip() + "\n\n" + readme_section
        ok = commit_file("README.md", new_readme, commit_msg, branch)
        print(f"  {'✓' if ok else '✗'} README.md (appended)")
        if ok:
            committed.append("README.md")
    elif readme_section:
        ok = commit_file("README.md", readme_section, commit_msg, branch)
        if ok:
            committed.append("README.md")

    # Append to requirements.txt
    if new_requirements and existing_reqs:
        existing_pkgs = set(l.split("==")[0].split(">=")[0].strip().lower()
                           for l in existing_reqs.splitlines() if l.strip() and not l.startswith("#"))
        to_add = [r for r in new_requirements
                  if r.split("==")[0].split(">=")[0].strip().lower() not in existing_pkgs]
        if to_add:
            new_reqs = existing_reqs.rstrip() + "\n" + "\n".join(to_add) + "\n"
            ok = commit_file("requirements.txt", new_reqs, commit_msg, branch)
            print(f"  {'✓' if ok else '✗'} requirements.txt (appended {len(to_add)} packages)")
            if ok:
                committed.append("requirements.txt")

    # Update src/auth/__init__.py
    if new_exports and existing_init:
        additions = "\n".join(f"from src.auth.{files[0].get('path','').split('/')[-1].replace('.py','')} import {e}"
                              for e in new_exports if e not in existing_init)
        if additions:
            new_init = existing_init.rstrip() + "\n" + additions + "\n"
            ok = commit_file("src/auth/__init__.py", new_init, commit_msg, branch)
            print(f"  {'✓' if ok else '✗'} src/auth/__init__.py (updated)")
            if ok:
                committed.append("src/auth/__init__.py")

    # Open PR
    print(f"\nOpening PR...")
    pr_title = f"[{ticket}] {summary}"
    pr_num, pr_url = create_pr(pr_title, pr_body, branch)
    if pr_num:
        print(f"✅ PR #{pr_num} opened: {pr_url}")
    else:
        print("Failed to open PR")
        sys.exit(1)

    print(f"\nDone! Branch: {branch}, PR: #{pr_num}")
    print(f"Files committed: {', '.join(committed)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticket",   required=True)
    parser.add_argument("--summary",  required=True)
    parser.add_argument("--feedback", default="")
    args = parser.parse_args()
    implement_ticket(args.ticket, args.summary, args.feedback)
