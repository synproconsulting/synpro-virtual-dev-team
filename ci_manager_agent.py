"""
ci_manager_agent.py
────────────────────
Self-contained Manager Agent for GitHub Actions.
Reviews a PR and merges it if CI passes and code quality is good.
No dependency on local agent framework — calls Anthropic API directly.

Usage:
    python ci_manager_agent.py --pr 8
"""

import os
import sys
import json
import argparse
import requests
import anthropic

# ── Config from environment ────────────────────────────────────────────────────

ANTHROPIC_KEY  = os.environ["ANTHROPIC_API_KEY"]
GITHUB_TOKEN   = os.environ["GITHUB_TOKEN"]
GITHUB_USERNAME = os.environ["GITHUB_USERNAME"]
GITHUB_REPO    = os.environ["GITHUB_REPO"]
JIRA_BASE_URL  = os.environ.get("JIRA_BASE_URL", "")
JIRA_EMAIL     = os.environ.get("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")

GH_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
JIRA_AUTH = (JIRA_EMAIL, JIRA_API_TOKEN)
JIRA_HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}
BASE = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}"


# ── GitHub helpers ─────────────────────────────────────────────────────────────

def get_pr(pr_number):
    r = requests.get(f"{BASE}/pulls/{pr_number}", headers=GH_HEADERS)
    r.raise_for_status()
    return r.json()

def get_ci_status(sha):
    r = requests.get(f"{BASE}/commits/{sha}/check-runs", headers=GH_HEADERS)
    runs = r.json().get("check_runs", [])
    results = []
    for run in runs:
        if run["name"] in ("Wait for CI then review", "Manager Agent review"):
            continue
        results.append({
            "name":       run["name"],
            "status":     run["status"],
            "conclusion": run.get("conclusion"),
        })
    return results

def get_pr_files(pr_number):
    r = requests.get(f"{BASE}/pulls/{pr_number}/files", headers=GH_HEADERS)
    return r.json()

def get_pr_diff(pr_number):
    headers = {**GH_HEADERS, "Accept": "application/vnd.github.v3.diff"}
    r = requests.get(f"{BASE}/pulls/{pr_number}", headers=headers)
    return r.text[:6000] + "\n...(truncated)" if len(r.text) > 6000 else r.text

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


# ── Main review logic ──────────────────────────────────────────────────────────

def review_pr(pr_number: int):
    print(f"\n=== Manager Agent reviewing PR #{pr_number} ===\n")

    # 1. Get PR details
    pr    = get_pr(pr_number)
    title = pr["title"]
    body  = pr.get("body", "")
    branch = pr["head"]["ref"]
    sha   = pr["head"]["sha"]
    mergeable = pr.get("mergeable")

    print(f"Title:     {title}")
    print(f"Branch:    {branch}")
    print(f"Mergeable: {mergeable}")

    # 2. Check CI
    checks = get_ci_status(sha)
    all_pass = all(
        c["conclusion"] in ("success", "skipped")
        for c in checks if c["status"] == "completed"
    )
    ci_summary = "\n".join(
        f"  {'✓' if c['conclusion']=='success' else '✗'} {c['name']}: {c['conclusion']}"
        for c in checks
    )
    print(f"\nCI Status:\n{ci_summary}")

    if not all_pass:
        print("\nCI not fully passing — skipping merge")
        post_comment(pr_number, "⚠️ Manager Agent: CI checks not all passing — skipping auto-merge.")
        return

    if mergeable is False:
        print("\nPR has merge conflicts — skipping merge")
        post_comment(pr_number, "⚠️ Manager Agent: PR has merge conflicts — please rebase.")
        return

    # 3. Get diff for Claude to review
    diff  = get_pr_diff(pr_number)
    files = get_pr_files(pr_number)
    file_list = "\n".join(f"  {f['filename']} (+{f['additions']} -{f['deletions']})" for f in files)

    # 4. Ask Claude to review the code
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    prompt = f"""You are a Dev Manager reviewing a pull request. 

PR #{pr_number}: {title}
Branch: {branch}

Files changed:
{file_list}

CI Results:
{ci_summary}

Code diff (truncated):
{diff}

Review this PR and respond with a JSON object:
{{
  "decision": "APPROVE" or "REQUEST_CHANGES",
  "summary": "one paragraph summary of the code quality",
  "issues": ["list of issues if any"],
  "merge_message": "squash commit message if approving"
}}

Respond ONLY with the JSON object, no other text."""

    print("\nAsking Claude to review the code...")
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:-1])

    try:
        review = json.loads(raw)
    except json.JSONDecodeError:
        print(f"Could not parse Claude response: {raw[:200]}")
        review = {"decision": "REQUEST_CHANGES", "summary": raw, "issues": [], "merge_message": ""}

    decision = review.get("decision", "REQUEST_CHANGES")
    summary  = review.get("summary", "")
    issues   = review.get("issues", [])

    print(f"\nReview decision: {decision}")
    print(f"Summary: {summary}")

    # 5. Extract Jira ticket from PR title
    import re
    ticket_match = re.search(r'\[([A-Z]+-\d+)\]', title)
    ticket_key   = ticket_match.group(1) if ticket_match else None
    print(f"Jira ticket: {ticket_key}")

    # 6. Act on decision
    if decision == "APPROVE":
        merge_title   = review.get("merge_message", title)
        merge_body    = f"Auto-merged by Manager Agent.\n\n{summary}"

        ok, result = merge_pr(pr_number, merge_title, merge_body)
        if ok:
            print(f"\n✅ PR #{pr_number} merged successfully")
            post_comment(pr_number,
                f"✅ **Manager Agent approved and merged this PR.**\n\n{summary}")

            if ticket_key:
                transitioned = jira_transition(ticket_key, "Done")
                print(f"Jira {ticket_key} → Done: {transitioned}")
                jira_comment(ticket_key,
                    f"PR #{pr_number} merged by Manager Agent.\n\n{summary}")
        else:
            print(f"\n✗ Merge failed: {result}")
            post_comment(pr_number, f"⚠️ Manager Agent: merge failed — {result.get('message','unknown error')}")

    else:
        issue_list = "\n".join(f"- {i}" for i in issues) if issues else "See summary above."
        comment = f"**Manager Agent — Changes Requested:**\n\n{summary}\n\n**Issues:**\n{issue_list}"
        post_comment(pr_number, comment)
        print(f"\nChanges requested on PR #{pr_number}")

        if ticket_key:
            jira_comment(ticket_key, f"PR #{pr_number} needs rework: {summary}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", type=int, required=True)
    args = parser.parse_args()
    review_pr(args.pr)
