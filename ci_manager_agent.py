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
    return diff[:12000] + "\n...(truncated)" if len(diff) > 12000 else diff

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
        print("PR has merge conflicts — closing and retriggering")
        requests.patch(f"{BASE}/pulls/{pr_number}", headers=GH_HEADERS,
                      json={"state": "closed"})
        # Try to extract ticket key from branch
        branch_match = re.search(r'feature/([a-z0-9]+-\d+)-', branch)
        t_key = branch_match.group(1).upper() if branch_match else None
        if t_key:
            clean_title = title
            for pat in [f"[{t_key}]", f"[***-{t_key.split('-')[1]}]"]:
                clean_title = clean_title.replace(pat, "").strip()
            jira_comment(t_key,
                f"PR #{pr_number} had merge conflicts and was closed. Retriggering.")
            requests.post(
                f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/actions/workflows/auto-implement.yml/dispatches",
                headers=GH_HEADERS,
                json={"ref": "main", "inputs": {
                    "ticket": t_key,
                    "summary": clean_title,
                    "feedback": "Previous PR had merge conflicts. Create files in control-centre/ directory only. Do not touch any shared files.",
                }}
            )
            print(f"Auto Implement retriggered for {t_key}")
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
        "APPROVAL CRITERIA - approve if ANY of these are true:\n"
        "- Tests pass and new source files are present\n"
        "- CI blocking jobs (Test, Security, E2E) all pass\n\n"
        "NEVER reject for these reasons:\n"
        "- SonarCloud skipped (always expected)\n"
        "- Railway deploy skipped (always expected)\n"
        "- Truncated diff\n"
        "- README changes\n"
        "- Mergeable shows None (GitHub still computing)\n\n"
        "ONLY reject for: hardcoded secrets, syntax errors, zero tests\n\n"
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

    # Try title first, fall back to branch name (title may be redacted in CI logs)
    ticket_match = re.search(r'\[([A-Z][A-Z0-9]+-\d+)\]', title)
    if ticket_match:
        ticket_key = ticket_match.group(1)
    else:
        branch_match = re.search(r'feature/([a-z0-9]+-\d+)-', branch)
        ticket_key = branch_match.group(1).upper() if branch_match else None
    print(f"Jira ticket key: {ticket_key}")

    if decision == "APPROVE":
        merge_title = review.get("merge_message", title)

        import time

        # Check if mergeable — wait for GitHub to compute it
        if mergeable is None:
            print("Waiting for GitHub to compute mergeability...")
            for _ in range(6):
                time.sleep(5)
                pr = get_pr(pr_number)
                mergeable = pr.get("mergeable")
                if mergeable is not None:
                    break
            print(f"Mergeable: {mergeable}")

        if mergeable is False:
            print("PR has merge conflicts — closing and retriggering")
            requests.patch(f"{BASE}/pulls/{pr_number}", headers=GH_HEADERS,
                          json={"state": "closed"})
            if ticket_key:
                jira_comment(ticket_key,
                    f"PR #{pr_number} had merge conflicts and was closed. Retriggering implementation.")
                requests.post(
                    f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/actions/workflows/auto-implement.yml/dispatches",
                    headers=GH_HEADERS,
                    json={"ref": "main", "inputs": {
                        "ticket": ticket_key,
                        "summary": pr["title"].replace(f"[{ticket_key}] ", "").strip(),
                        "feedback": "Previous PR had merge conflicts. Implement fresh from latest main branch. Only create new files.",
                    }}
                )
                print(f"Auto Implement retriggered for {ticket_key}")
            return

        ok, result = merge_pr(pr_number, merge_title, f"Auto-merged by Manager Agent.\n\n{summary}")
        if ok:
            print(f"\n✅ PR #{pr_number} merged")
            post_comment(pr_number, f"✅ **Manager Agent merged this PR.**\n\n{summary}")
            if ticket_key:
                print(f"Updating Jira {ticket_key}...")
                transitioned = jira_transition(ticket_key, "Done")
                print(f"  Transition result: {transitioned}")
                jira_comment(ticket_key, f"PR #{pr_number} merged by Manager Agent.\n\n{summary}")
                print(f"  Comment posted")
            else:
                print("No Jira ticket key found in PR title")
        else:
            print(f"\n✗ Merge failed: {result}")
            # If still conflicted, close and retrigger via Auto Implement
            if "conflict" in str(result).lower() or "405" in str(result):
                print("Merge conflicts detected — closing PR and triggering reimplement")
                requests.patch(f"{BASE}/pulls/{pr_number}", headers=GH_HEADERS,
                             json={"state": "closed"})
                if ticket_key:
                    jira_comment(ticket_key,
                        f"PR #{pr_number} had merge conflicts and was closed. Will be reimplemented.")
                    # Trigger Auto Implement
                    requests.post(
                        f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/actions/workflows/auto-implement.yml/dispatches",
                        headers=GH_HEADERS,
                        json={"ref": "main", "inputs": {
                            "ticket": ticket_key,
                            "summary": pr["title"].replace(f"[{ticket_key}] ", "").strip(),
                            "feedback": "Previous PR had merge conflicts. Implement fresh from main branch.",
                        }}
                    )
                    print(f"Auto Implement triggered for {ticket_key}")
            else:
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
