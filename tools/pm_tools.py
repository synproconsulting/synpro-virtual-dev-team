"""
tools/pm_tools.py
─────────────────
CrewAI-compatible tool wrappers around jira_client.
Each class is a self-contained tool the PM Agent can call by name.
"""

from crewai.tools import BaseTool  # crewai >= 1.0
from pydantic import BaseModel, Field
from typing import Optional
from tools import jira_client as jira


# ── Input schemas ──────────────────────────────────────────────────────────────

class NoInput(BaseModel):
    pass


class CreateEpicInput(BaseModel):
    summary: str     = Field(...)
    description: str = Field("")


class CreateStoryInput(BaseModel):
    summary:         str           = Field(...)
    description:     str           = Field("")
    epic_key:        Optional[str] = Field(None)
    story_points:    Optional[int] = Field(None)
    priority:        str           = Field("Medium")
    execution_order: Optional[int] = Field(None, description="Execution order for dependency sequencing, stored in customfield_10071. Required on every story.")


class UpdateIssueInput(BaseModel):
    issue_key:    str           = Field(...)
    summary:      Optional[str] = Field(None)
    description:  Optional[str] = Field(None)
    priority:     Optional[str] = Field(None)
    story_points: Optional[int] = Field(None)


class TransitionInput(BaseModel):
    issue_key:   str = Field(...)
    status_name: str = Field(...)


class CommentInput(BaseModel):
    issue_key: str = Field(...)
    body:      str = Field(...)


class CreateSprintInput(BaseModel):
    name:       str           = Field(...)
    goal:       str           = Field("")
    start_date: Optional[str] = Field(None)
    end_date:   Optional[str] = Field(None)


class AddToSprintInput(BaseModel):
    sprint_id:  int       = Field(...)
    issue_keys: list[str] = Field(...)


class CreateIssueLinkInput(BaseModel):
    blocker_issue_key: str = Field(..., description="The issue that blocks another issue")
    blocked_issue_key: str = Field(..., description="The issue that is blocked")


class ListIssueLinksInput(BaseModel):
    issue_key: str = Field(...)


class CreateOrGetFixVersionInput(BaseModel):
    name: str = Field(..., description="Version name (e.g., 'v1.0.0', 'Sprint 1 Release')")
    description: str = Field("", description="Optional version description")
    release_date: Optional[str] = Field(None, description="Optional release date in ISO format (YYYY-MM-DD)")
    released: bool = Field(False, description="Whether the version is already released")


# ── Tool classes ───────────────────────────────────────────────────────────────

class ListBacklogTool(BaseTool):
    name:        str = "list_backlog"
    description: str = "List all issues currently in the project backlog (not assigned to any sprint)."
    args_schema: type = NoInput

    def _run(self, **_) -> str:
        issues = jira.list_backlog()
        if not issues:
            return "Backlog is empty."
        return "\n".join(jira.format_issue(i) for i in issues)


class ListAllIssuesTool(BaseTool):
    name:        str = "list_all_issues"
    description: str = "List all open issues in the project regardless of sprint."
    args_schema: type = NoInput

    def _run(self, **_) -> str:
        issues = jira.list_all_issues()
        if not issues:
            return "No open issues found."
        return "\n".join(jira.format_issue(i) for i in issues)


class CreateEpicTool(BaseTool):
    name:        str = "create_epic"
    description: str = "Create a new Epic in Jira. Returns the new epic key."
    args_schema: type = CreateEpicInput

    def _run(self, summary: str, description: str = "") -> str:
        result = jira.create_epic(summary, description)
        key = result.get("key", "unknown")
        return f"Epic created: {key} — {summary}"


class CreateStoryTool(BaseTool):
    name:        str = "create_story"
    description: str = (
        "Create a new Story in Jira. Optionally link to an Epic with epic_key. "
        "Returns the new story key."
    )
    args_schema: type = CreateStoryInput

    def _run(self, summary: str, description: str = "",
             epic_key: Optional[str] = None,
             story_points: Optional[int] = None,
             priority: str = "Medium",
             execution_order: Optional[int] = None) -> str:
        result = jira.create_story(summary, description, epic_key, story_points, priority, execution_order)
        key = result.get("key", "unknown")
        order_str = f" (execution order: {execution_order})" if execution_order else ""
        return f"Story created: {key} — {summary}{order_str}"


class UpdateIssueTool(BaseTool):
    name:        str = "update_issue"
    description: str = "Update the summary, description, priority, or story points of an existing issue."
    args_schema: type = UpdateIssueInput

    def _run(self, issue_key: str, summary=None, description=None,
             priority=None, story_points=None) -> str:
        jira.update_issue(issue_key, summary, description, priority, story_points)
        return f"Issue {issue_key} updated successfully."


class TransitionIssueTool(BaseTool):
    name:        str = "transition_issue"
    description: str = "Move an issue to a new workflow status, e.g. 'In Progress' or 'Done'."
    args_schema: type = TransitionInput

    def _run(self, issue_key: str, status_name: str) -> str:
        jira.transition_issue(issue_key, status_name)
        return f"Issue {issue_key} moved to '{status_name}'."


class AddCommentTool(BaseTool):
    name:        str = "add_comment"
    description: str = "Post a comment on a Jira issue."
    args_schema: type = CommentInput

    def _run(self, issue_key: str, body: str) -> str:
        jira.add_comment(issue_key, body)
        return f"Comment posted on {issue_key}."


class ListSprintsTool(BaseTool):
    name:        str = "list_sprints"
    description: str = "List all active and future sprints for the project board."
    args_schema: type = NoInput

    def _run(self, **_) -> str:
        sprints = jira.list_sprints()
        if not sprints:
            return "No active or future sprints found."
        lines = []
        for s in sprints:
            lines.append(f"[{s['id']}] {s['name']} — state: {s['state']} | goal: {s.get('goal','')}")
        return "\n".join(lines)


class CreateSprintTool(BaseTool):
    name:        str = "create_sprint"
    description: str = (
        "Create a new sprint on the project board. "
        "Provide ISO-8601 dates (e.g. 2025-05-01T09:00:00.000Z) for scheduling."
    )
    args_schema: type = CreateSprintInput

    def _run(self, name: str, goal: str = "",
             start_date: Optional[str] = None,
             end_date: Optional[str] = None) -> str:
        result = jira.create_sprint(name, goal, start_date, end_date)
        sprint_id = result.get("id", "unknown")
        return f"Sprint created: ID={sprint_id} — {name}"


class AddToSprintTool(BaseTool):
    name:        str = "add_issues_to_sprint"
    description: str = "Move a list of backlog issues into a specific sprint by sprint ID."
    args_schema: type = AddToSprintInput

    def _run(self, sprint_id: int, issue_keys: list[str]) -> str:
        jira.add_issues_to_sprint(sprint_id, issue_keys)
        return f"Added {issue_keys} to sprint {sprint_id}."


class CreateBlockerLinkTool(BaseTool):
    name:        str = "create_blocker_link"
    description: str = (
        "Create a 'blocks' relationship between two issues. "
        "The blocker_issue_key blocks the blocked_issue_key. "
        "Use this to establish dependencies where one story must be completed before another can begin."
    )
    args_schema: type = CreateIssueLinkInput

    def _run(self, blocker_issue_key: str, blocked_issue_key: str) -> str:
        jira.create_issue_link(
            inward_issue_key=blocked_issue_key,
            outward_issue_key=blocker_issue_key,
            link_type="Blocks"
        )
        return f"{blocker_issue_key} now blocks {blocked_issue_key}"


class ListIssueLinksToolImpl(BaseTool):
    name:        str = "list_issue_links"
    description: str = "List all issue links (blocks, is-blocked-by, relates-to, etc.) for a given issue."
    args_schema: type = ListIssueLinksInput

    def _run(self, issue_key: str) -> str:
        links = jira.list_issue_links(issue_key)
        if not links:
            return f"No links found for {issue_key}."
        
        lines = [f"Links for {issue_key}:"]
        for link in links:
            lines.append(
                f"  • {link['relationship']} {link['related_issue']} ({link['link_type']})"
            )
        return "\n".join(lines)


class ListFixVersionsTool(BaseTool):
    name:        str = "list_fix_versions"
    description: str = "List all fix versions (releases) for the project."
    args_schema: type = NoInput

    def _run(self, **_) -> str:
        versions = jira.list_fix_versions()
        if not versions:
            return "No fix versions found."
        
        lines = ["Fix Versions:"]
        for v in versions:
            released_status = "Released" if v["released"] else "Unreleased"
            release_date = f" | Release: {v['release_date']}" if v.get("release_date") else ""
            lines.append(f"  • [{v['id']}] {v['name']} — {released_status}{release_date}")
        return "\n".join(lines)


class CreateOrGetFixVersionTool(BaseTool):
    name:        str = "create_or_get_fix_version"
    description: str = (
        "Get an existing fix version by name, or create it if it doesn't exist. "
        "This ensures deterministic version IDs — calling with the same name always returns the same ID. "
        "Use this when you need to assign issues to a specific release version."
    )
    args_schema: type = CreateOrGetFixVersionInput

    def _run(self, name: str, description: str = "",
             release_date: Optional[str] = None,
             released: bool = False) -> str:
        result = jira.create_or_get_fix_version(name, description, release_date, released)
        
        action = "Created" if result["created"] else "Found existing"
        return f"{action} fix version: ID={result['id']} — {result['name']}"


# ── Tool groups (keep each group small to stay within Claude schema limits) ────

BACKLOG_TOOLS = [
    ListBacklogTool(),
    ListAllIssuesTool(),
    CreateEpicTool(),
    CreateStoryTool(),
    UpdateIssueTool(),
    CreateBlockerLinkTool(),
    ListIssueLinksToolImpl(),
]

VERSION_TOOLS = [
    ListFixVersionsTool(),
    CreateOrGetFixVersionTool(),
]

SPRINT_TOOLS = [
    ListSprintsTool(),
    CreateSprintTool(),
    AddToSprintTool(),
    AddCommentTool(),
    TransitionIssueTool(),
]

ALL_PM_TOOLS = BACKLOG_TOOLS + VERSION_TOOLS + SPRINT_TOOLS
