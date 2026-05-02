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
from typing import Optional, Tuple

# ── Config ─────────────────────────────────────────────────────────────────────

ANTHROPIC_KEY   = os.environ["ANTHROPIC_API_KEY"]
GITHUB_TOKEN    = os.environ["GITHUB_TOKEN"]
PAT_TOKEN       = os.environ.get("PAT_TOKEN", GITHUB_TOKEN)  # PAT can dispatch workflows; GITHUB_TOKEN cannot
GITHUB_USERNAME = os.environ["GITHUB_USERNAME"]
GITHUB_REPO     = os.environ["GITHUB_REPO"]
JIRA_BASE_URL   = os.environ.get("JIRA_BASE_URL", "")
JIRA_EMAIL      = os.environ.get("JIRA_EMAIL", "")
JIRA_API_TOKEN  = os.environ.get("JIRA_API_TOKEN", "")

# Maximum number of times to retrigger Auto Implement before failing
# This prevents infinite loops when merge conflicts repeatedly occur
MAX_RETRIGGER_ATTEMPTS = int(os.environ.get("MAX_RETRIGGER_ATTEMPTS", "3"))

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
SKIP_JOBS    = {"Manager Agent review", "Wait for CI then review", "wait-and-review"}


# ── GitHub helpers ─────────────────────────────────────────────────────────────

def get_pr(pr_number: int) -> dict:
    """Fetch PR details from GitHub."""
    r = requests.get(f"{BASE}/pulls/{pr_number}", headers=GH_HEADERS)
    r.raise_for_status()
    return r.json()

def get_ci_status(sha: str) -> list:
    """Get all CI check runs for a commit, excluding Manager Agent jobs."""
    r = requests.get(f"{BASE}/commits/{sha}/check-runs", headers=GH_HEADERS)
    runs = r.json().get("check_runs", [])
    return [c for c in runs if c["name"] not in SKIP_JOBS]

def wait_for_ci(sha: str, max_minutes: int = 15) -> bool:
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

def get_pr_diff(pr_number: int) -> str:
    """Fetch PR diff, truncated to 12KB for Claude."""
    headers = {**GH_HEADERS, "Accept": "application/vnd.github.v3.diff"}
    r = requests.get(f"{BASE}/pulls/{pr_number}", headers=headers)
    diff = r.text
    return diff[:12000] + "\n...(truncated)" if len(diff) > 12000 else diff

def get_pr_files(pr_number: int) -> list:
    """Fetch list of files changed in PR."""
    r = requests.get(f"{BASE}/pulls/{pr_number}/files", headers=GH_HEADERS)
    return r.json()

def post_comment(pr_number: int, body: str) -> None:
    """Post a comment on a PR."""
    requests.post(f"{BASE}/issues/{pr_number}/comments",
                  headers=GH_HEADERS, json={"body": body})

def get_retrigger_count(ticket_key: str) -> int:
    """
    Count how many times Auto Implement has been triggered for this ticket.
    Looks at closed PRs to count previous retrigger attempts.
    """
    try:
        # Search for all PRs (open and closed) matching this ticket
        r = requests.get(
            f"{BASE}/pulls",
            headers=GH_HEADERS,
            params={"state": "all", "per_page": 100}
        )
        if not r.ok:
            return 0
        
        prs = r.json()
        count = 0
        
        for pr in prs:
            branch = pr.get("head", {}).get("ref", "")
            title = pr.get("title", "")
            
            # Match ticket in branch name or title
            if ticket_key.lower() in branch.lower() or ticket_key in title:
                # Check if this PR was closed due to conflicts (has retrigger comment)
                comments_url = pr.get("comments_url", "")
                if comments_url:
                    comments_r = requests.get(comments_url, headers=GH_HEADERS)
                    if comments_r.ok:
                        comments = comments_r.json()
                        for comment in comments:
                            body = comment.get("body", "")
                            if "Merge conflict detected" in body or "retriggering" in body.lower():
                                count += 1
                                break
        
        return count
    except Exception as e:
        print(f"Warning: Could not determine retrigger count: {e}")
        return 0

def trigger_auto_implement(
    ticket_key: str,
    summary: str,
    feedback: str,
    pr_number: Optional[int] = None
) -> bool:
    """
    Dispatch Auto Implement using PAT_TOKEN, which can trigger workflow_dispatch.
    GITHUB_TOKEN cannot trigger other workflows (GitHub security restriction).
    
    Returns True if triggered successfully, False if retrigger cap reached or failed.
    """
    # Check retrigger count before attempting
    retrigger_count = get_retrigger_count(ticket_key)
    
    if retrigger_count >= MAX_RETRIGGER_ATTEMPTS:
        msg = (
            f"🛑 **Manager Agent: Retrigger cap reached ({MAX_RETRIGGER_ATTEMPTS} attempts)**\n\n"
            f"This ticket `{ticket_key}` has been retriggered {retrigger_count} times due to merge conflicts.\n"
            f"Manual intervention is required to resolve the underlying issue.\n\n"
            f"**Possible causes:**\n"
            f"- Persistent conflicts with files being modified by other PRs\n"
            f"- Ticket requires changes to shared infrastructure files\n"
            f"- Implementation strategy needs manual adjustment\n\n"
            f"**Next steps:**\n"
            f"1. Review the merge conflicts in the closed PRs\n"
            f"2. Manually implement the ticket or adjust the requirements\n"
            f"3. Check if dependencies need to be updated in Jira"
        )
        print(f"RETRIGGER CAP REACHED for {ticket_key}: {retrigger_count} attempts")
        
        if pr_number:
            post_comment(pr_number, msg)
        
        # Post to Jira
        jira_comment(
            ticket_key,
            f"Auto Implement retrigger cap reached after {retrigger_count} attempts. "
            f"Manual intervention required. See PR #{pr_number} for details."
        )
        
        return False
    
    # Log retrigger attempt
    attempt_num = retrigger_count + 1
    print(f"Triggering Auto Implement for {ticket_key} (attempt {attempt_num}/{MAX_RETRIGGER_ATTEMPTS})")
    
    r = requests.post(
        f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/actions/workflows/auto-implement.yml/dispatches",
        headers=DISPATCH_HEADERS,
        json={"ref": "main", "inputs": {"ticket": ticket_key, "summary": summary, "feedback": feedback}},
    )
    
    if r.status_code == 204:
        print(f"Auto Implement triggered for {ticket_key} (attempt {attempt_num}/{MAX_RETRIGGER_ATTEMPTS})")
        
        # Post status update to PR if available
        if pr_number:
            post_comment(
                pr_number,
                f"🔄 **Auto Implement retriggered** (attempt {attempt_num}/{MAX_RETRIGGER_ATTEMPTS})\n\n"
                f"A fresh implementation will be created from the latest `main` branch."
            )
        
        return True
    else:
        msg = (
            f"⚠️ **Manager Agent: Auto Implement retrigger failed** (HTTP {r.status_code}) — "
            f"manual intervention required for `{ticket_key}`.\n\nResponse: `{r.text[:200]}`"
        )
        print(f"Auto Implement retrigger FAILED: {r.status_code} {r.text[:200]}")
        if pr_number:
            post_comment(pr_number, msg)
        return False

def merge_pr(pr_number: int, title: str, message: str) -> Tuple[bool, dict]:
    """
    Merge a PR using squash merge.
    
    Must use PAT_TOKEN (DISPATCH_HEADERS), not GITHUB_TOKEN.
    GitHub does not fire push events for merges performed by GITHUB_TOKEN,
    so CI and Railway deploy would never trigger after a Manager Agent merge.
    """
    r = requests.put(f"{BASE}/pulls/{pr_number}/merge", headers=DISPATCH_HEADERS, json={
        "commit_title":   title,
        "commit_message": message,
        "merge_method":   "squash",
    })
    return r.ok, r.json()


# ── Jira helpers ───────────────────────────────────────────────────────────────

def jira_transition(issue_key: str, status_name: str = "Done") -> bool:
    """Transition a Jira issue to a new status."""
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

def jira_comment(issue_key: str, body: str) -> None:
    """Post a comment on a Jira issue."""
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

def review_pr(pr_number: int, sha: Optional[str] = None) -> None:
    """
    Main review logic for Manager Agent.
    
    Reviews a PR, runs AI review, handles merge conflicts,
    and manages retriggers with loop prevention.
    """
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
        post_comment(pr_number,
            f"⚠️ **Manager Agent: Merge conflict detected.**\n\n"
            f"This PR cannot be merged due to conflicts with `main`. "
            f"Closing and retriggering Auto Implement to create a fresh implementation from latest main.")
        requests.patch(f"{BASE}/pulls/{pr_number}", headers=GH_HEADERS,
                      json={"state": "closed"})
        branch_match = re.search(r'feature/([a-z0-9]+-\d+)-', branch)
        t_key = branch_match.group(1).upper() if branch_match else None
        if t_key:
            clean_title = title
            for pat in [f"[{t_key}]", f"[***-{t_key.split('-')[1]}]"]:
                clean_title = clean_title.replace(pat, "").strip()
            jira_comment(t_key,
                f"PR #{pr_number} had merge conflicts and was closed. Retriggering.")
            trigger_auto_implement(
                t_key, clean_title,
                "Previous PR had merge conflicts. Create files in control-centre/ directory only. Do not touch any shared files.",
                pr_number,
            )
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
            post_comment(pr_number,
                f"⚠️ **Manager Agent: Merge conflict detected.**\n\n"
                f"This PR cannot be merged due to conflicts with `main`. "
                f"Closing and retriggering Auto Implement to create a fresh implementation from latest main.")
            requests.patch(f"{BASE}/pulls/{pr_number}", headers=GH_HEADERS,
                          json={"state": "closed"})
            if ticket_key:
                jira_comment(ticket_key,
                    f"PR #{pr_number} had merge conflicts and was closed. Retriggering implementation.")
                trigger_auto_implement(
                    ticket_key,
                    pr["title"].replace(f"[{ticket_key}] ", "").strip(),
                    "Previous PR had merge conflicts. Implement fresh from latest main branch. Only create new files.",
                    pr_number,
                )
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
                post_comment(pr_number,
                    f"⚠️ **Manager Agent: Merge failed due to conflict.**\n\n"
                    f"Closing and retriggering Auto Implement to create a fresh implementation from latest main.")
                requests.patch(f"{BASE}/pulls/{pr_number}", headers=GH_HEADERS,
                             json={"state": "closed"})
                if ticket_key:
                    jira_comment(ticket_key,
                        f"PR #{pr_number} had merge conflicts and was closed. Will be reimplemented.")
                    trigger_auto_implement(
                        ticket_key,
                        pr["title"].replace(f"[{ticket_key}] ", "").strip(),
                        "Previous PR had merge conflicts. Implement fresh from main branch.",
                        pr_number,
                    )
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
