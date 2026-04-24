"""
ci_manager_agent.py
────────────────────
Self-contained Manager Agent for GitHub Actions.
Handles CI waiting, code review, merge, and Jira updates.

Usage:
    python ci_manager_agent.py --pr 8        # review specific PR
    python ci_manager_agent.py --auto        # auto mode (reads from env)
"""

import os
import sys
import json
import time
import argparse
import re
import requests
import anthropic

# ── Config ─────────────────────────────────────────────────────────────────────

ANTHROPIC_KEY   = os.environ["ANTHROPIC_API_KEY"]
GITHUB_TOKEN    = os.environ["GITHUB_TOKEN"]
GITHUB_USERNAME = os.environ["GITHUB_USERNAME"]
GITHUB_REPO     = os.environ["GITHUB_REPO"]
JIRA_BASE_URL   = os.environ.get("JIRA_BASE_URL", "")
JIRA_EMAIL      = os.environ.get("JIRA_EMAIL", "")
JIRA_API_TOKEN  = os.environ.get("JIRA_API_TOKEN", "")

GH_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
JIRA_AUTH    = (JIRA_EMAIL, JIRA_API_TOKEN)
JIRA_HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}
BASE         = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}"
SKIP_JOBS    = {"Manager Agent review", "Wait for CI then review", "wait-and-review"}


# ── GitHub helpers ─────────────────────────────────────────────────────────────

def get_pr(pr_number):
    r = requests.get(f"{BASE}/pulls/{pr_number}", headers=GH_HEADERS)
    r.raise_for_status()
    return r.json()

def get_ci_status(sha):
    r = requests.get(f"{BASE}/commits/{sha}/check-runs", headers=GH_HEADERS)
    runs = r.json().get("check_runs", [])
    return [c for c in runs if c["name"] not in SKIP_JOBS]

def wait_for_ci(sha, max_minutes=15):
    """Wait for all CI checks to complete. Returns True if all pass."""
    print(f"Waiting for CI checks on sha: {sha[:8]}")
    for attempt in range(max_minutes * 6):
        time.sleep(10)
        checks   = get_ci_status(sha)
        total    = len(checks)
        done     = sum(1 for c in checks if c["status"] == "completed")
        failed   = sum(1 for c in checks if c.get("conclusion") in ("failure", "cancelled", "timed_out"))
        print(f"  Attempt {attempt+1}: {done}/{total} completed, {failed} failed")
        if total > 0 and done == total:
            return failed == 0
    return False

def get_pr_diff(pr_number):
    headers = {**GH_HEADERS, "Accept": "application/vnd.github.v3.diff"}
    r = requests.get(f"{BASE}/pulls/{pr_number}", headers=headers)
    diff = r.text
    return diff[:6000] + "\n...(truncated)" if len(diff) > 6000 else diff

def get_pr_files(pr_number):
    r = requests.get(f"{BASE}/pulls/{pr_number}/files", headers=GH_HEADERS)
    return r.json()

def post_comment(pr_number, body):
    requests.post(f"{BASE}/issues/{pr_number}/comments",
                  headers=GH_HEADERS, json={"body": body})

def merge_pr(pr_number, title, message):
    r = requests.put(f"{BASE}/pulls/{pr_number}/merge", headers=GH_HEADERS, json={
        "commit_title":   title,
        "commit_message": message,
        "merge_method":   "squash",
    })
    return r.ok, r.json()


# ── Jira helpers ───────────────────────────────────────────────────────────────

def jira_transition(issue_key, status_name="Done"):
    if not JIRA_BASE_URL:
        return False
    r = requests.get(
        f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions",
        headers=JIRA_HEADERS, auth=JIRA_AUTH
    )
    transitions = r.json().get("transitions", [])
    match = next((t for t in transitions if t["name"].lower() == status_name.lower()), None)
    if not match:
        return False
    r2 = requests.post(
        f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions",
        headers=JIRA_HEADERS, auth=JIRA_AUTH,
        json={"transition": {"id": match["id"]}}
    )
    return r2.status_code in (200, 204)

def jira_comment(issue_key, body):
    if not JIRA_BASE_URL:
        return
    requests.post(
        f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment",
        headers=JIRA_HEADERS, auth=JIRA_AUTH,
        json={"body": {"type": "doc", "version": 1, "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": body}]}
        ]}}
    )


# ── Review logic ───────────────────────────────────────────────────────────────

def review_pr(pr_number, sha=None):
    print(f"\n=== Manager Agent reviewing PR #{pr_number} ===\n")

    pr        = get_pr(pr_number)
    title     = pr["title"]
    branch    = pr["head"]["ref"]
    sha       = sha or pr["head"]["sha"]
    mergeable = pr.get("mergeable")

    print(f"Title:     {title}")
    print(f"Branch:    {branch}")
    print(f"Mergeable: {mergeable}")

    if mergeable is False:
        print("PR has merge conflicts — skipping")
        post_comment(pr_number, "⚠️ Manager Agent: merge conflicts present — please rebase.")
        return

    checks     = get_ci_status(sha)
    all_pass   = all(c.get("conclusion") in ("success", "skipped") for c in checks if c["status"] == "completed")
    ci_summary = "\n".join(
        f"  {'✓' if c.get('conclusion')=='success' else '✗'} {c['name']}: {c.get('conclusion','pending')}"
        for c in checks
    ) or "  No CI checks found"
    print(f"\nCI:\n{ci_summary}")

    if not all_pass:
        print("CI not fully passing — skipping")
        post_comment(pr_number, f"⚠️ Manager Agent: CI not passing — skipping merge.\n\n```\n{ci_summary}\n```")
        return

    diff  = get_pr_diff(pr_number)
    files = get_pr_files(pr_number)
    file_list = "\n".join(f"  {f['filename']} (+{f['additions']} -{f['deletions']})" for f in files)

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    prompt = (
        f"You are a Dev Manager reviewing PR #{pr_number}: {title}\n\n"
        f"Files changed:\n{file_list}\n\n"
        f"CI:\n{ci_summary}\n\n"
        f"Diff:\n{diff}\n\n"
        "Respond ONLY with a JSON object:\n"
        '{"decision":"APPROVE" or "REQUEST_CHANGES","summary":"one paragraph","issues":[],"merge_message":"commit title"}'
    )

    print("\nAsking Claude to review...")
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:-1])

    try:
        review = json.loads(raw)
    except json.JSONDecodeError:
        review = {"decision": "REQUEST_CHANGES", "summary": raw, "issues": [], "merge_message": ""}

    decision = review.get("decision", "REQUEST_CHANGES")
    summary  = review.get("summary", "")
    issues   = review.get("issues", [])
    print(f"\nDecision: {decision}")
    print(f"Summary:  {summary}")

    ticket_match = re.search(r'\[([A-Z]+-\d+)\]', title)
    ticket_key   = ticket_match.group(1) if ticket_match else None

    if decision == "APPROVE":
        merge_title = review.get("merge_message", title)
        ok, result  = merge_pr(pr_number, merge_title, f"Auto-merged by Manager Agent.\n\n{summary}")
        if ok:
            print(f"\n✅ PR #{pr_number} merged")
            post_comment(pr_number, f"✅ **Manager Agent merged this PR.**\n\n{summary}")
            if ticket_key:
                jira_transition(ticket_key, "Done")
                jira_comment(ticket_key, f"PR #{pr_number} merged by Manager Agent.\n\n{summary}")
                print(f"Jira {ticket_key} → Done")
        else:
            print(f"\n✗ Merge failed: {result}")
            post_comment(pr_number, f"⚠️ Manager Agent: merge failed — {result.get('message','unknown')}")
    else:
        issue_list = "\n".join(f"- {i}" for i in issues)
        post_comment(pr_number, f"**Manager Agent — Changes Requested:**\n\n{summary}\n\n{issue_list}")
        if ticket_key:
            jira_comment(ticket_key, f"PR #{pr_number} needs rework: {summary}")
        print("Changes requested")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr",   type=int, help="PR number to review")
    parser.add_argument("--auto", action="store_true", help="Auto mode — reads PR from environment")
    args = parser.parse_args()

    if args.auto:
        event     = os.environ.get("EVENT_NAME", "")
        manual_pr = os.environ.get("MANUAL_PR", "").strip()
        pr_env    = os.environ.get("PR_NUMBER", "").strip()
        head_sha  = os.environ.get("HEAD_SHA", "").strip()

        if manual_pr:
            pr_num = int(manual_pr)
            sha    = None
        elif pr_env:
            pr_num = int(pr_env)
            sha    = head_sha or None
            if sha:
                print("Waiting for CI to complete...")
                ci_ok = wait_for_ci(sha)
                if not ci_ok:
                    print("CI failed or timed out — skipping Manager Agent")
                    sys.exit(0)
        else:
            print("No PR number found — nothing to review")
            sys.exit(0)

        review_pr(pr_num, sha=None)

    elif args.pr:
        review_pr(args.pr)
    else:
        print("Use --pr <number> or --auto")
        sys.exit(1)
