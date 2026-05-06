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
from tools.validation import validate_execution_order, validate_story_creation


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


class StartSprintInput(BaseModel):
    sprint_id: int = Field(..., description="The numeric ID of the sprint to start")


class AddToSprintInput(BaseModel):
    sprint_id:  int       = Field(...)
    issue_keys: list[str] = Field(...)


class CreateIssueLinkInput(BaseModel):
    blocker_issue_key: str = Field(..., description="The issue that blocks another issue")
    blocked_issue_key: str = Field(..., description="The issue that is blocked")


class ListIssueLinksInput(BaseModel):
    issue_key: str = Field(...)


class CreateOrGetFixVersionInput(BaseModel):
    name:         str           = Field(..., description="The version name (must be unique within the project)")
    description:  str           = Field("", description="Optional description of the version/release")
    release_date: Optional[str] = Field(None, description="Optional release date in YYYY-MM-DD format")
    archived:     bool          = Field(False, description="Whether the version is archived")
    released:     bool          = Field(False, description="Whether the version has been released")


class ListFixVersionsInput(BaseModel):
    include_archived: bool = Field(False, description="Whether to include archived versions")
    include_released: bool = Field(True, description="Whether to include released versions")


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
        "⚠️  IMPORTANT: Always set execution_order — stories without it will not be processed by the Orchestrator. "
        "Returns the new story key."
    )
    args_schema: type = CreateStoryInput

    def _run(self, summary: str, description: str = "",
             epic_key: Optional[str] = None,
             story_points: Optional[int] = None,
             priority: str = "Medium",
             execution_order: Optional[int] = None) -> str:
        
        # Validate before creating
        warnings = validate_story_creation(summary, epic_key, execution_order)
        
        # Create the story
        result = jira.create_story(summary, description, epic_key, story_points, priority, execution_order)
        key = result.get("key", "unknown")
        
        # Build response with warnings
        order_str = f" (execution order: {execution_order})" if execution_order else ""
        response_parts = [f"Story created: {key} — {summary}{order_str}"]
        
        # Add validation warnings to the response so the agent is informed
        if warnings:
            response_parts.append("\n\n" + "\n".join(warnings))
        
        return "".join(response_parts)


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


class StartSprintTool(BaseTool):
    name:        str = "start_sprint"
    description: str = (
        "Start (activate) a sprint by its ID. This transitions the sprint from 'future' state to 'active' state. "
        "Use this after creating a sprint and adding issues to it, once the team is ready to begin work. "
        "The sprint must have start_date and end_date set before it can be started. "
        "Only one sprint can be active at a time per board."
    )
    args_schema: type = StartSprintInput

    def _run(self, sprint_id: int) -> str:
        try:
            result = jira.start_sprint(sprint_id)
            return (
                f"Sprint started successfully!\n"
                f"  ID: {result['id']}\n"
                f"  Name: {result['name']}\n"
                f"  State: {result['state']}\n"
                f"  Start: {result.get('start_date', 'N/A')}\n"
                f"  End: {result.get('end_date', 'N/A')}"
            )
        except ValueError as e:
            return f"Failed to start sprint: {str(e)}"
        except Exception as e:
            return f"Error starting sprint: {str(e)}"


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


class CreateOrGetFixVersionTool(BaseTool):
    name:        str = "create_or_get_fix_version"
    description: str = (
        "Create a new fix version (release) or retrieve an existing one with the same name. "
        "This tool is idempotent - calling it multiple times with the same name will return "
        "the same fix version ID. Use this for release planning and tracking which features "
        "go into which releases. The returned ID is deterministic and can be used to tag issues."
    )
    args_schema: type = CreateOrGetFixVersionInput

    def _run(self, name: str, description: str = "",
             release_date: Optional[str] = None,
             archived: bool = False,
             released: bool = False) -> str:
        result = jira.create_or_get_fix_version(
            name=name,
            description=description,
            release_date=release_date,
            archived=archived,
            released=released
        )
        
        action = "created" if result.get("created") else "found existing"
        version_id = result.get("id", "unknown")
        version_name = result.get("name", name)
        
        output_lines = [f"Fix version {action}: {version_name} (ID: {version_id})"]
        
        if description:
            output_lines.append(f"  Description: {description}")
        
        if release_date:
            output_lines.append(f"  Release date: {release_date}")
        
        if archived:
            output_lines.append("  Status: Archived")
        elif released:
            output_lines.append("  Status: Released")
        else:
            output_lines.append("  Status: Unreleased")
        
        return "\n".join(output_lines)


class ListFixVersionsTool(BaseTool):
    name:        str = "list_fix_versions"
    description: str = (
        "List all fix versions (releases) in the project. "
        "Use this to see existing versions before creating new ones."
    )
    args_schema: type = ListFixVersionsInput

    def _run(self, include_archived: bool = False,
             include_released: bool = True) -> str:
        versions = jira.list_fix_versions(
            include_archived=include_archived,
            include_released=include_released
        )
        
        if not versions:
            return "No fix versions found."
        
        lines = ["Fix versions:"]
        for v in versions:
            status_parts = []
            if v.get("released"):
                status_parts.append("Released")
            if v.get("archived"):
                status_parts.append("Archived")
            
            status = ", ".join(status_parts) if status_parts else "Unreleased"
            
            line = f"  [{v['id']}] {v['name']} — {status}"
            
            if v.get("release_date"):
                line += f" | Release: {v['release_date']}"
            
            if v.get("description"):
                line += f" | {v['description']}"
            
            lines.append(line)
        
        return "\n".join(lines)


# ── Tool groups (keep each group small to stay within Claude schema limits) ────

BACKLOG_TOOLS = [
    ListBacklogTool(),
    ListAllIssuesTool(),
    CreateEpicTool(),
    CreateStoryTool(),
    UpdateIssueTool(),
    CreateBlockerLinkTool(),
    ListIssueLinksToolImpl(),
    CreateOrGetFixVersionTool(),
    ListFixVersionsTool(),
]

SPRINT_TOOLS = [
    ListSprintsTool(),
    CreateSprintTool(),
    StartSprintTool(),
    AddToSprintTool(),
    AddCommentTool(),
    TransitionIssueTool(),
]

ALL_PM_TOOLS = BACKLOG_TOOLS + SPRINT_TOOLS
