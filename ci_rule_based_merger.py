"""
ci_rule_based_merger.py
────────────────────────
Rule-based PR auto-merger for GitHub Actions.
Merges purely on CI results — no Anthropic API calls.

Blocking CI jobs (must pass): Test (Python 3.11), Test (Python 3.12), Security scan
All other jobs are non-blocking (Playwright E2E, Railway deploy, SonarCloud, etc.).

Usage:
    python ci_rule_based_merger.py --pr 8        # process specific PR
    python ci_rule_based_merger.py --auto        # auto mode (reads from env)
"""

import os
import sys
import time
import argparse
import re
import requests

# ── Config ─────────────────────────────────────────────────────────────────────

GITHUB_TOKEN    = os.environ["GITHUB_TOKEN"]
PAT_TOKEN       = os.environ.get("PAT_TOKEN", GITHUB_TOKEN)
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
DISPATCH_HEADERS = {
    "Authorization": f"token {PAT_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
JIRA_AUTH    = (JIRA_EMAIL, JIRA_API_TOKEN)
JIRA_HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}
BASE         = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}"

SKIP_JOBS = {"Manager Agent review", "Wait for CI then review", "wait-and-review"}
BLOCKING_JOBS = {"Test (Python 3.11)", "Test (Python 3.12)", "Security scan"}


# ── GitHub helpers ─────────────────────────────────────────────────────────────

def get_pr(pr_number):
    r = requests.get(f"{BASE}/pulls/{pr_number}", headers=GH_HEADERS)
    r.raise_for_status()
    return r.json()

def get_ci_checks(sha):
    r = requests.get(f"{BASE}/commits/{sha}/check-runs", headers=GH_HEADERS)
    runs = r.json().get("check_runs", [])
    return [c for c in runs if c["name"] not in SKIP_JOBS]

def wait_for_ci(sha, max_minutes=30):
    """Poll check-runs every 10 sec until all complete or max_minutes elapsed.
    Returns (all_complete, checks)."""
    print(f"Polling CI checks on sha: {sha[:8]} (max {max_minutes} min)")
    for attempt in range(max_minutes * 6):
        time.sleep(10)
        checks = get_ci_checks(sha)
        total  = len(checks)
        done   = sum(1 for c in checks if c["status"] == "completed")
        print(f"  Attempt {attempt + 1}: {done}/{total} completed")
        if total > 0 and done == total:
            print("  All CI checks complete.")
            return True, checks
    print(f"  CI wait timed out after {max_minutes} minutes — evaluating current state")
    return False, get_ci_checks(sha)

def checks_summary(checks):
    return "\n".join(
        f"  {'✓' if c.get('conclusion') in ('success', 'skipped') else '✗'} {c['name']}: {c.get('conclusion', 'pending')}"
        for c in checks
    ) or "  No CI checks found"

def blocking_checks_pass(checks):
    """Evaluate only BLOCKING_JOBS. Returns (passed, results_dict, failed_names).
    Returns passed=False if no blocking jobs were found at all."""
    results = {c["name"]: c.get("conclusion", "pending")
               for c in checks if c["name"] in BLOCKING_JOBS}
    failed  = [name for name, conclusion in results.items()
               if conclusion not in ("success", "skipped")]
    return len(failed) == 0 and len(results) > 0, results, failed

def post_comment(pr_number, body):
    requests.post(f"{BASE}/issues/{pr_number}/comments",
                  headers=GH_HEADERS, json={"body": body})

def merge_pr(pr_number, title, message):
    # Must use PAT_TOKEN (DISPATCH_HEADERS) — GITHUB_TOKEN merges do not fire push events,
    # so CI and Railway deploy would never trigger after merge.
    r = requests.put(f"{BASE}/pulls/{pr_number}/merge", headers=DISPATCH_HEADERS, json={
        "commit_title":   title,
        "commit_message": message,
        "merge_method":   "squash",
    })
    return r.ok, r.json()

def trigger_auto_implement(ticket_key, summary, feedback, pr_number=None):
    """Dispatch auto-implement.yml via PAT_TOKEN — GITHUB_TOKEN cannot trigger workflow_dispatch."""
    r = requests.post(
        f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/actions/workflows/auto-implement.yml/dispatches",
        headers=DISPATCH_HEADERS,
        json={"ref": "main", "inputs": {"ticket": ticket_key, "summary": summary, "feedback": feedback}},
    )
    if r.status_code == 204:
        print(f"Auto Implement triggered for {ticket_key}")
    else:
        msg = (f"⚠️ **Rule-based merger: Auto Implement retrigger failed** (HTTP {r.status_code}) — "
               f"manual intervention required for `{ticket_key}`.\n\nResponse: `{r.text[:200]}`")
        print(f"Auto Implement retrigger FAILED: {r.status_code} {r.text[:200]}")
        if pr_number:
            post_comment(pr_number, msg)


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


# ── Merge logic ────────────────────────────────────────────────────────────────

def extract_ticket_key(title, branch):
    m = re.search(r'\[([A-Z][A-Z0-9]+-\d+)\]', title)
    if m:
        return m.group(1)
    m = re.search(r'feature/([a-z0-9]+-\d+)-', branch)
    return m.group(1).upper() if m else None

def handle_merge_conflict(pr_number, pr, ticket_key):
    title = pr["title"]
    print("Merge conflict detected — closing PR and retriggering Auto Implement")
    post_comment(pr_number,
        f"⚠️ **Rule-based merger: Merge conflict detected.**\n\n"
        f"This PR cannot be merged due to conflicts with `main`. "
        f"Closing and retriggering Auto Implement to create a fresh implementation from latest main.")
    requests.patch(f"{BASE}/pulls/{pr_number}", headers=GH_HEADERS, json={"state": "closed"})
    if ticket_key:
        clean_title = title.replace(f"[{ticket_key}]", "").strip()
        jira_comment(ticket_key, f"PR #{pr_number} had merge conflicts and was closed. Retriggering.")
        trigger_auto_implement(
            ticket_key, clean_title,
            "Previous PR had merge conflicts. Implement fresh from latest main branch.",
            pr_number,
        )

def process_pr(pr_number, sha=None):
    print(f"\n=== Rule-based merger processing PR #{pr_number} ===\n")

    pr        = get_pr(pr_number)
    title     = pr["title"]
    branch    = pr["head"]["ref"]
    sha       = sha or pr["head"]["sha"]
    mergeable = pr.get("mergeable")

    print(f"Title:     {title}")
    print(f"Branch:    {branch}")
    print(f"Mergeable: {mergeable}")

    ticket_key = extract_ticket_key(title, branch)
    print(f"Jira ticket: {ticket_key}")

    if mergeable is False:
        handle_merge_conflict(pr_number, pr, ticket_key)
        return

    all_done, checks = wait_for_ci(sha, max_minutes=30)
    summary = checks_summary(checks)
    print(f"\nCI:\n{summary}")

    passes, results, failed_jobs = blocking_checks_pass(checks)

    if not passes:
        if not results:
            msg = ("⚠️ **Rule-based merger: No blocking CI checks found — not merging.**\n\n"
                   "Expected blocking jobs (`Test (Python 3.11)`, `Test (Python 3.12)`, "
                   "`Security scan`) were not found in check-runs.\n\n"
                   f"```\n{summary}\n```")
        else:
            failed_list = "\n".join(f"- `{name}`: {results[name]}" for name in failed_jobs)
            msg = (f"⚠️ **Rule-based merger: CI failed — not merging.**\n\n"
                   f"The following blocking CI jobs did not pass:\n{failed_list}\n\n"
                   f"Full CI summary:\n```\n{summary}\n```")
        print(f"Not merging — blocking jobs failed or missing: {failed_jobs or 'none found'}")
        post_comment(pr_number, msg)
        return

    print("All blocking CI jobs passed — checking mergeability")

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
        handle_merge_conflict(pr_number, pr, ticket_key)
        return

    ok, result = merge_pr(pr_number, title, "Auto-merged by rule-based merger (CI passed).")
    if ok:
        print(f"\n✅ PR #{pr_number} merged")
        post_comment(pr_number, "✅ **Rule-based merger: PR merged.**\n\nAll blocking CI checks passed.")
        if ticket_key:
            print(f"Updating Jira {ticket_key}...")
            transitioned = jira_transition(ticket_key, "Done")
            print(f"  Transition: {transitioned}")
            jira_comment(ticket_key, f"PR #{pr_number} merged by rule-based merger. All CI checks passed.")
        else:
            print("No Jira ticket key found in PR title or branch")
    else:
        print(f"\n✗ Merge failed: {result}")
        if "conflict" in str(result).lower():
            handle_merge_conflict(pr_number, pr, ticket_key)
        else:
            post_comment(pr_number, f"⚠️ Rule-based merger: merge failed — {result.get('message', 'unknown')}")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr",   type=int, help="PR number to process")
    parser.add_argument("--auto", action="store_true", help="Auto mode — reads PR from environment")
    args = parser.parse_args()

    if args.auto:
        manual_pr = os.environ.get("MANUAL_PR", "").strip()
        pr_env    = os.environ.get("PR_NUMBER", "").strip()
        head_sha  = os.environ.get("HEAD_SHA", "").strip()

        if manual_pr:
            process_pr(int(manual_pr))
        elif pr_env:
            process_pr(int(pr_env), sha=head_sha or None)
        else:
            print("No PR number found — nothing to process")
            sys.exit(0)

    elif args.pr:
        process_pr(args.pr)
    else:
        print("Use --pr <number> or --auto")
        sys.exit(1)
