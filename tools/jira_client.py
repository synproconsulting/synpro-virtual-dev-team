"""
tools/jira_client.py
────────────────────
Low-level Jira REST API client for PM Agent tooling.
Wraps JIRA Python library calls with project-specific defaults.
"""

import os
from typing import Any, Optional
from jira import JIRA


# ── Connection ─────────────────────────────────────────────────────────────────

def _get_client() -> JIRA:
    """Lazy singleton connection to Jira Cloud."""
    if not hasattr(_get_client, "_instance"):
        jira_url = os.environ.get("JIRA_URL")
        jira_email = os.environ.get("JIRA_EMAIL")
        jira_api_token = os.environ.get("JIRA_API_TOKEN")
        
        if not all([jira_url, jira_email, jira_api_token]):
            raise ValueError(
                "Missing required Jira environment variables: "
                "JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN"
            )
        
        _get_client._instance = JIRA(
            server=jira_url,
            basic_auth=(jira_email, jira_api_token),
        )
    return _get_client._instance


def _get_project_key() -> str:
    """Return the default project key from environment."""
    key = os.environ.get("JIRA_PROJECT_KEY")
    if not key:
        raise ValueError("JIRA_PROJECT_KEY environment variable not set")
    return key


def _get_board_id() -> int:
    """Return the default board ID from environment."""
    board_id = os.environ.get("JIRA_BOARD_ID")
    if not board_id:
        raise ValueError("JIRA_BOARD_ID environment variable not set")
    return int(board_id)


# ── Formatters ─────────────────────────────────────────────────────────────────

def format_issue(issue: Any) -> str:
    """Format a Jira issue for display in agent output."""
    key = issue.key
    summary = issue.fields.summary
    issue_type = issue.fields.issuetype.name
    status = issue.fields.status.name
    
    # Custom fields
    story_points = getattr(issue.fields, "customfield_10016", None)
    execution_order = getattr(issue.fields, "customfield_10071", None)
    
    parts = [f"[{key}] {issue_type}: {summary} — Status: {status}"]
    
    if story_points is not None:
        parts.append(f" | SP: {story_points}")
    
    if execution_order is not None:
        parts.append(f" | Order: {execution_order}")
    
    # Parent epic link
    epic_link = getattr(issue.fields, "customfield_10014", None) or getattr(issue.fields, "parent", None)
    if epic_link:
        epic_key = epic_link.key if hasattr(epic_link, "key") else epic_link
        parts.append(f" | Epic: {epic_key}")
    
    return "".join(parts)


# ── Backlog & Issues ───────────────────────────────────────────────────────────

def list_backlog() -> list[Any]:
    """List all issues in the backlog (not assigned to any sprint)."""
    jira = _get_client()
    project_key = _get_project_key()
    
    jql = f"project = {project_key} AND sprint is EMPTY AND resolution = Unresolved ORDER BY created DESC"
    return jira.search_issues(jql, maxResults=100)


def list_all_issues() -> list[Any]:
    """List all open issues in the project regardless of sprint."""
    jira = _get_client()
    project_key = _get_project_key()
    
    jql = f"project = {project_key} AND resolution = Unresolved ORDER BY created DESC"
    return jira.search_issues(jql, maxResults=200)


# ── Epic & Story Creation ──────────────────────────────────────────────────────

def create_epic(summary: str, description: str = "") -> dict[str, Any]:
    """Create a new Epic in Jira."""
    jira = _get_client()
    project_key = _get_project_key()
    
    fields = {
        "project": {"key": project_key},
        "summary": summary,
        "description": description,
        "issuetype": {"name": "Epic"},
    }
    
    issue = jira.create_issue(fields=fields)
    return {"key": issue.key, "id": issue.id}


def create_story(
    summary: str,
    description: str = "",
    epic_key: Optional[str] = None,
    story_points: Optional[int] = None,
    priority: str = "Medium",
    execution_order: Optional[int] = None,
) -> dict[str, Any]:
    """Create a new Story in Jira, optionally linked to an Epic."""
    jira = _get_client()
    project_key = _get_project_key()
    
    fields: dict[str, Any] = {
        "project": {"key": project_key},
        "summary": summary,
        "description": description,
        "issuetype": {"name": "Story"},
        "priority": {"name": priority},
    }
    
    if story_points is not None:
        fields["customfield_10016"] = story_points
    
    if execution_order is not None:
        fields["customfield_10071"] = execution_order
    
    # Epic link (field name varies by Jira setup)
    if epic_key:
        # Try parent field first (newer Jira), fall back to epic link custom field
        try:
            fields["parent"] = {"key": epic_key}
        except Exception:
            fields["customfield_10014"] = epic_key
    
    issue = jira.create_issue(fields=fields)
    return {"key": issue.key, "id": issue.id}


# ── Update & Transition ────────────────────────────────────────────────────────

def update_issue(
    issue_key: str,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    story_points: Optional[int] = None,
) -> None:
    """Update fields on an existing issue."""
    jira = _get_client()
    issue = jira.issue(issue_key)
    
    fields: dict[str, Any] = {}
    
    if summary is not None:
        fields["summary"] = summary
    
    if description is not None:
        fields["description"] = description
    
    if priority is not None:
        fields["priority"] = {"name": priority}
    
    if story_points is not None:
        fields["customfield_10016"] = story_points
    
    if fields:
        issue.update(fields=fields)


def transition_issue(issue_key: str, status_name: str) -> None:
    """Transition an issue to a new workflow status."""
    jira = _get_client()
    issue = jira.issue(issue_key)
    
    # Find the transition ID matching the target status
    transitions = jira.transitions(issue)
    transition_id = None
    
    for t in transitions:
        if t["name"].lower() == status_name.lower() or t["to"]["name"].lower() == status_name.lower():
            transition_id = t["id"]
            break
    
    if not transition_id:
        raise ValueError(f"No transition found to status '{status_name}' for {issue_key}")
    
    jira.transition_issue(issue, transition_id)


def add_comment(issue_key: str, body: str) -> None:
    """Add a comment to an issue."""
    jira = _get_client()
    jira.add_comment(issue_key, body)


# ── Issue Links (Blocks / Is Blocked By) ───────────────────────────────────────

def create_issue_link(
    inward_issue_key: str,
    outward_issue_key: str,
    link_type: str = "Blocks",
) -> None:
    """Create a directional link between two issues.
    
    Args:
        inward_issue_key: The issue on the 'inward' side of the link
        outward_issue_key: The issue on the 'outward' side of the link
        link_type: The link type name (e.g., 'Blocks', 'Relates', 'Duplicate')
    
    For 'Blocks' link type:
        - If A blocks B: create_issue_link(inward_issue_key=B, outward_issue_key=A, link_type='Blocks')
        - This makes A appear as "blocks" B, and B appears as "is blocked by" A
    
    Note: Jira link types have directionality with inward/outward descriptions.
    """
    jira = _get_client()
    jira.create_issue_link(
        type=link_type,
        inwardIssue=inward_issue_key,
        outwardIssue=outward_issue_key,
    )


def list_issue_links(issue_key: str) -> list[dict[str, Any]]:
    """Retrieve all links for a given issue.
    
    Returns a list of dictionaries with:
        - link_type: The name of the link type
        - direction: 'inward' or 'outward'
        - related_issue: The key of the linked issue
        - relationship: Human-readable relationship (e.g., 'blocks', 'is blocked by')
    """
    jira = _get_client()
    issue = jira.issue(issue_key)
    
    links = []
    for link in issue.fields.issuelinks:
        link_type = link.type.name
        
        if hasattr(link, "outwardIssue"):
            links.append({
                "link_type": link_type,
                "direction": "outward",
                "related_issue": link.outwardIssue.key,
                "relationship": link.type.outward,
            })
        
        if hasattr(link, "inwardIssue"):
            links.append({
                "link_type": link_type,
                "direction": "inward",
                "related_issue": link.inwardIssue.key,
                "relationship": link.type.inward,
            })
    
    return links


# ── Sprint Management ──────────────────────────────────────────────────────────

def list_sprints() -> list[dict[str, Any]]:
    """List all active and future sprints for the board."""
    jira = _get_client()
    board_id = _get_board_id()
    
    sprints = jira.sprints(board_id, state="active,future")
    
    result = []
    for sprint in sprints:
        result.append({
            "id": sprint.id,
            "name": sprint.name,
            "state": sprint.state,
            "goal": getattr(sprint, "goal", ""),
            "start_date": getattr(sprint, "startDate", None),
            "end_date": getattr(sprint, "endDate", None),
        })
    
    return result


def create_sprint(
    name: str,
    goal: str = "",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict[str, Any]:
    """Create a new sprint on the board."""
    jira = _get_client()
    board_id = _get_board_id()
    
    sprint_data: dict[str, Any] = {
        "name": name,
        "boardId": board_id,
    }
    
    if goal:
        sprint_data["goal"] = goal
    
    if start_date:
        sprint_data["startDate"] = start_date
    
    if end_date:
        sprint_data["endDate"] = end_date
    
    sprint = jira.create_sprint(**sprint_data)
    
    return {
        "id": sprint.id,
        "name": sprint.name,
        "state": sprint.state,
    }


def add_issues_to_sprint(sprint_id: int, issue_keys: list[str]) -> None:
    """Move issues from backlog into a sprint."""
    jira = _get_client()
    jira.add_issues_to_sprint(sprint_id, issue_keys)


# ── Fix Version Management ─────────────────────────────────────────────────────

def create_or_get_fix_version(
    name: str,
    description: str = "",
    release_date: Optional[str] = None,
    archived: bool = False,
    released: bool = False,
) -> dict[str, Any]:
    """Create or retrieve a fix version with deterministic ID.
    
    This function ensures idempotent fix version creation by checking if a version
    with the given name already exists before creating a new one.
    
    Args:
        name: The version name (must be unique within the project)
        description: Optional description of the version/release
        release_date: Optional release date in YYYY-MM-DD format
        archived: Whether the version is archived (default: False)
        released: Whether the version has been released (default: False)
    
    Returns:
        A dictionary containing:
            - id: The fix version ID (numeric string)
            - name: The version name
            - description: The version description
            - archived: Whether the version is archived
            - released: Whether the version is released
            - release_date: The release date if set
            - created: Boolean indicating if the version was newly created (True) or already existed (False)
    
    Raises:
        ValueError: If JIRA_PROJECT_KEY environment variable is not set
    """
    jira = _get_client()
    project_key = _get_project_key()
    
    # First, try to find an existing version with this name
    project = jira.project(project_key)
    existing_versions = jira.project_versions(project)
    
    for version in existing_versions:
        if version.name == name:
            # Version already exists, return it
            return {
                "id": version.id,
                "name": version.name,
                "description": getattr(version, "description", ""),
                "archived": getattr(version, "archived", False),
                "released": getattr(version, "released", False),
                "release_date": getattr(version, "releaseDate", None),
                "created": False,
            }
    
    # Version doesn't exist, create it
    version_data: dict[str, Any] = {
        "name": name,
        "project": project_key,
        "archived": archived,
        "released": released,
    }
    
    if description:
        version_data["description"] = description
    
    if release_date:
        version_data["releaseDate"] = release_date
    
    new_version = jira.create_version(**version_data)
    
    return {
        "id": new_version.id,
        "name": new_version.name,
        "description": getattr(new_version, "description", ""),
        "archived": getattr(new_version, "archived", False),
        "released": getattr(new_version, "released", False),
        "release_date": getattr(new_version, "releaseDate", None),
        "created": True,
    }


def list_fix_versions(
    include_archived: bool = False,
    include_released: bool = True,
) -> list[dict[str, Any]]:
    """List all fix versions in the project.
    
    Args:
        include_archived: Whether to include archived versions (default: False)
        include_released: Whether to include released versions (default: True)
    
    Returns:
        A list of dictionaries, each containing:
            - id: The fix version ID
            - name: The version name
            - description: The version description
            - archived: Whether the version is archived
            - released: Whether the version is released
            - release_date: The release date if set
    """
    jira = _get_client()
    project_key = _get_project_key()
    
    project = jira.project(project_key)
    versions = jira.project_versions(project)
    
    result = []
    for version in versions:
        archived = getattr(version, "archived", False)
        released = getattr(version, "released", False)
        
        # Filter based on parameters
        if not include_archived and archived:
            continue
        if not include_released and released:
            continue
        
        result.append({
            "id": version.id,
            "name": version.name,
            "description": getattr(version, "description", ""),
            "archived": archived,
            "released": released,
            "release_date": getattr(version, "releaseDate", None),
        })
    
    return result
