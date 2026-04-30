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


# ── Tool groups (keep each group small to stay within Claude schema limits) ────

BACKLOG_TOOLS = [
    ListBacklogTool(),
    ListAllIssuesTool(),
    CreateEpicTool(),
    CreateStoryTool(),
    UpdateIssueTool(),
]

SPRINT_TOOLS = [
    ListSprintsTool(),
    CreateSprintTool(),
    AddToSprintTool(),
    AddCommentTool(),
    TransitionIssueTool(),
]

ALL_PM_TOOLS = BACKLOG_TOOLS + SPRINT_TOOLS
