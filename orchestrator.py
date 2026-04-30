"""
orchestrator.py
───────────────
Sprint Orchestrator — Serial execution, one ticket at a time.

For each ticket (in dependency order):
1. Trigger Auto Implement (GitHub Actions)
2. Wait for PR to open (up to 5 min)
3. Wait for CI to pass (up to 15 min)
4. Trigger Auto Review (GitHub Actions)
5. Wait for PR to merge (up to 5 min)
6. Move to next ticket

Usage:
    python main.py --agent sprint
    python main.py --agent sprint --dry-run
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

load_dotenv()
console = Console()

# ── Validate environment ───────────────────────────────────────────────────────
_REQUIRED = ["JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN",
             "JIRA_PROJECT_KEY", "ANTHROPIC_API_KEY",
             "GITHUB_TOKEN", "GITHUB_USERNAME", "GITHUB_REPO"]
missing = [k for k in _REQUIRED if not os.environ.get(k)]
if missing:
    console.print(f"[red]Missing environment variables: {missing}[/red]")
    sys.exit(1)

os.environ["OPENAI_API_KEY"] = "sk-no-openai-needed"

import tools.jira_client as jira
import tools.github_client as gh_tools

TOKEN    = os.environ["GITHUB_TOKEN"]
USERNAME = os.environ["GITHUB_USERNAME"]
REPO     = os.environ["GITHUB_REPO"]
GH_HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
BASE = f"https://api.github.com/repos/{USERNAME}/{REPO}"

# TODO SDT1-52: remove this list when Orchestrator resume is implemented — dead weight from Sprint 4,
# harmless but misleading. All Sprint 5+ tickets use customfield_10071 directly.
# Execution order for Sprint 4 (dependency chain)
EXECUTION_ORDER = [
    "SDT1-31",  # 1. Dashboard foundation
    "SDT1-36",  # 2. Dependency management
    "SDT1-33",  # 3. Workflow monitor
    "SDT1-29",  # 4. Sprint trigger + Auto Review
    "SDT1-30",  # 5. UAT deployment
    "SDT1-28",  # 6. SonarCloud
    "SDT1-35",  # 7. PM Agent planning
]


# ── Jira helpers ───────────────────────────────────────────────────────────────

def get_open_sprint_tickets():
    """Fetch To Do tickets from Jira, sorted by execution order field."""
    SKIP_TYPES = {"Epic", "Sub-task", "Subtask"}
    issues = jira.list_all_issues(max_results=100)
    tickets = [
        {
            "key":             i["key"],
            "summary":         i["fields"]["summary"],
            "priority":        i["fields"].get("priority", {}).get("name", "Medium"),
            "issuetype":       i["fields"].get("issuetype", {}).get("name", "Story"),
            "execution_order": i["fields"].get("customfield_10071") or 999,
        }
        for i in issues
        if i["fields"].get("issuetype", {}).get("name") not in SKIP_TYPES
        and i["fields"].get("status", {}).get("name", "") == "To Do"
    ]

    # Sort by Jira execution order field, fallback to hardcoded list
    def sort_key(t):
        if t["execution_order"] != 999:
            return t["execution_order"]
        try:
            return EXECUTION_ORDER.index(t["key"])
        except ValueError:
            return 999

    return sorted(tickets, key=sort_key)


# ── GitHub helpers ─────────────────────────────────────────────────────────────

def trigger_workflow(workflow_file, inputs):
    """Trigger a GitHub Actions workflow dispatch."""
    url = f"{BASE}/actions/workflows/{workflow_file}/dispatches"
    r = requests.post(url, headers=GH_HEADERS, json={"ref": "main", "inputs": inputs})
    return r.status_code == 204

def get_open_pr_for_ticket(ticket_key):
    """Find open PR number for this ticket."""
    prs = requests.get(f"{BASE}/pulls", headers=GH_HEADERS,
                       params={"state": "open"}).json()
    if not isinstance(prs, list):
        return None
    for pr in prs:
        branch = pr.get("head", {}).get("ref", "")
        title  = pr.get("title", "")
        if ticket_key.lower() in branch.lower() or ticket_key.upper() in title.upper():
            return pr["number"]
    return None

def get_pr_ci_status(pr_number):
    """Returns 'passing', 'failing', or 'pending'."""
    r = requests.get(f"{BASE}/pulls/{pr_number}", headers=GH_HEADERS)
    if not r.ok:
        return "pending"
    sha = r.json().get("head", {}).get("sha", "")
    if not sha:
        return "pending"

    checks_r = requests.get(f"{BASE}/commits/{sha}/check-runs", headers=GH_HEADERS)
    if not checks_r.ok:
        return "pending"

    SKIP = {"Manager Agent review", "wait-and-review"}
    runs = [c for c in checks_r.json().get("check_runs", [])
            if c["name"] not in SKIP]

    if not runs:
        return "pending"

    total     = len(runs)
    completed = sum(1 for c in runs if c["status"] == "completed")
    failed    = sum(1 for c in runs
                   if c.get("conclusion") in ("failure", "cancelled", "timed_out"))

    if completed == total:
        return "failing" if failed > 0 else "passing"
    return "pending"

def is_pr_closed_or_merged(pr_number):
    """Check if PR is merged or closed."""
    r = requests.get(f"{BASE}/pulls/{pr_number}", headers=GH_HEADERS)
    if not r.ok:
        return False
    pr = r.json()
    return pr.get("merged", False) or pr.get("state") == "closed"


# ── Serial ticket processor ────────────────────────────────────────────────────

def process_ticket(ticket):
    """Full serial pipeline for one ticket."""
    key     = ticket["key"]
    summary = ticket["summary"]

    console.print(f"\n[bold cyan]━━━ [{key}]: {summary[:60]} ━━━[/bold cyan]")

    # Step 1: Trigger Auto Implement
    console.print(f"  [cyan]1/5 Triggering Auto Implement...[/cyan]")
    ok = trigger_workflow("auto-implement.yml", {
        "ticket": key, "summary": summary, "feedback": ""
    })
    if not ok:
        console.print(f"  [red]✗ Failed to trigger Auto Implement[/red]")
        return "failed"
    console.print(f"  [green]✓ Auto Implement triggered[/green]")

    # Step 2: Wait for PR to open (5 min)
    console.print(f"  [cyan]2/5 Waiting for PR to open...[/cyan]")
    pr_number = None
    for i in range(30):
        time.sleep(10)
        pr_number = get_open_pr_for_ticket(key)
        if pr_number:
            console.print(f"  [green]✓ PR #{pr_number} opened[/green]")
            break
        if i % 6 == 5:
            console.print(f"  [dim]    Still waiting... ({(i+1)*10}s elapsed)[/dim]")

    if not pr_number:
        console.print(f"  [red]✗ No PR opened after 5 minutes — skipping[/red]")
        return "failed"

    # Step 3: Wait for CI (15 min)
    console.print(f"  [cyan]3/5 Waiting for CI on PR #{pr_number}...[/cyan]")
    ci_status = "pending"
    for i in range(90):
        time.sleep(10)
        ci_status = get_pr_ci_status(pr_number)
        if ci_status == "passing":
            console.print(f"  [green]✓ CI passing[/green]")
            break
        elif ci_status == "failing":
            console.print(f"  [red]✗ CI failing[/red]")
            return "ci_failed"
        if i % 6 == 5:
            console.print(f"  [dim]    CI: {ci_status} ({(i+1)*10}s elapsed)[/dim]")

    if ci_status == "pending":
        console.print(f"  [yellow]⚠ CI timeout — proceeding anyway[/yellow]")

    # Step 4: Trigger Auto Review
    console.print(f"  [cyan]4/5 Triggering Auto Review on PR #{pr_number}...[/cyan]")
    ok = trigger_workflow("auto-review.yml", {"pr_number": str(pr_number)})
    if not ok:
        console.print(f"  [red]✗ Failed to trigger Auto Review[/red]")
        return "failed"
    console.print(f"  [green]✓ Auto Review triggered[/green]")

    # Step 5: Wait for merge (10 min — allow time for conflict resolution + retry)
    console.print(f"  [cyan]5/5 Waiting for PR to merge...[/cyan]")
    for i in range(60):
        time.sleep(10)
        if is_pr_closed_or_merged(pr_number):
            console.print(f"  [green]✓ PR #{pr_number} merged/closed — [{key}] complete![/green]")
            return "merged"
        if i % 6 == 5:
            console.print(f"  [dim]    Waiting for merge... ({(i+1)*10}s elapsed)[/dim]")

    console.print(f"  [red]✗ PR #{pr_number} not merged after 10 min[/red]")
    return "merge_timeout"


# ── Main ───────────────────────────────────────────────────────────────────────

def run_sprint(max_agents=1, dry_run=False, review_only=False):

    console.print(Panel.fit(
        "[bold cyan]Virtual Dev Team — Sprint Orchestrator[/bold cyan]\n"
        "[yellow]Serial execution — one ticket at a time[/yellow]",
        border_style="cyan"
    ))

    console.print("\n[cyan]Fetching open sprint tickets from Jira...[/cyan]")
    tickets = get_open_sprint_tickets()

    if not tickets:
        console.print("[yellow]No open To Do tickets found in Jira.[/yellow]")
        return

    # Skipped epics message
    skipped = [t for t in jira.list_all_issues(max_results=100)
               if t["fields"].get("issuetype", {}).get("name") in {"Epic", "Sub-task", "Subtask"}
               and t["fields"].get("status", {}).get("name") == "To Do"]
    if skipped:
        console.print(f"[dim]Skipped {len(skipped)} non-implementable issues (Epics/Sub-tasks)[/dim]")

    # Display table
    table = Table(title=f"Open tickets ({len(tickets)} found) — execution order")
    table.add_column("Order",    style="dim")
    table.add_column("Key",      style="cyan")
    table.add_column("Summary",  style="white")
    table.add_column("Priority", style="yellow")
    for t in tickets:
        order = str(int(t["execution_order"])) if t["execution_order"] != 999 else "-"
        table.add_row(order, t["key"], t["summary"][:55], t["priority"])
    console.print(table)

    if dry_run:
        console.print("\n[yellow]Dry run — no agents will be started.[/yellow]")
        return

    # Re-query Jira before each ticket so the loop always works from current state.
    # This means a ticket moved to Done mid-run (by the Manager Agent or manually)
    # is never processed twice, and a resumed run never re-processes completed work.
    results = []
    while True:
        tickets = get_open_sprint_tickets()
        if not tickets:
            break

        ticket = tickets[0]  # lowest execution order among remaining To Do tickets
        console.print(f"\n[dim]── [{ticket['key']}] {len(tickets)} To Do ticket(s) remaining ──[/dim]")
        status = process_ticket(ticket)
        results.append({"ticket": ticket["key"], "status": status})

        if status == "merge_timeout":
            remaining = get_open_sprint_tickets()
            console.print(Panel(
                f"[bold red]Sprint halted — manual intervention required[/bold red]\n\n"
                f"[{ticket['key']}] PR did not merge within the 10-minute window.\n"
                f"[yellow]{len(remaining)} ticket(s) have NOT been started.[/yellow]\n\n"
                f"Steps to resume:\n"
                f"  1. Check the open PR on GitHub and resolve any issues\n"
                f"  2. Confirm the PR is merged\n"
                f"  3. Re-run the sprint — already-merged tickets will be skipped\n"
                f"     (their Jira status is Done, not To Do)",
                border_style="red"
            ))
            sys.exit(1)

        time.sleep(5)

    # Summary
    merged = sum(1 for r in results if r["status"] == "merged")
    failed = sum(1 for r in results if r["status"] in ("failed", "ci_failed"))

    console.print(Panel(
        f"[bold green]Sprint Complete[/bold green]\n\n"
        f"✓ Merged:  {merged}\n"
        f"✗ Failed:  {failed}",
        border_style="green"
    ))
