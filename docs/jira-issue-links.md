# Jira Issue Links: Blocks / Is Blocked By

## Overview

The PM Agent now supports creating and managing Jira issue links, specifically the "blocks" / "is blocked by" relationship. This allows the PM Agent to explicitly capture dependencies between stories, improving sprint planning and execution order management.

## Features

### 1. Create Blocker Links

The PM Agent can establish that one story blocks another story from being started or completed.

**Tool:** `create_blocker_link`

**Parameters:**
- `blocker_issue_key` (str): The issue that blocks another issue (e.g., "TEST-1")
- `blocked_issue_key` (str): The issue that is blocked (e.g., "TEST-2")

**Example:**
```python
# Story TEST-1 must be completed before TEST-2 can begin
create_blocker_link(
    blocker_issue_key="TEST-1",
    blocked_issue_key="TEST-2"
)
```

This creates a bidirectional link in Jira:
- TEST-1 shows: "blocks TEST-2"
- TEST-2 shows: "is blocked by TEST-1"

### 2. List Issue Links

The PM Agent can retrieve all links associated with an issue to understand its dependencies.

**Tool:** `list_issue_links`

**Parameters:**
- `issue_key` (str): The issue to retrieve links for

**Example:**
```python
list_issue_links(issue_key="TEST-2")
```

**Output:**
```
Links for TEST-2:
  • is blocked by TEST-1 (Blocks)
  • blocks TEST-3 (Blocks)
  • relates to TEST-4 (Relates)
```

## Use Cases

### Sprint Planning

When planning a sprint, the PM Agent should:

1. **Identify Dependencies**: Analyze which stories depend on others
2. **Create Links**: Use `create_blocker_link` to document these dependencies
3. **Set Execution Order**: Assign `execution_order` values that respect the dependency chain
4. **Validate**: Use `list_issue_links` to verify dependencies are correctly captured

**Example Workflow:**
```
Story A: "Create database schema"
Story B: "Implement data access layer" (depends on A)
Story C: "Build REST API" (depends on B)

Actions:
1. create_blocker_link(blocker_issue_key="A", blocked_issue_key="B")
2. create_blocker_link(blocker_issue_key="B", blocked_issue_key="C")
3. Set execution_order: A=1, B=2, C=3
```

### Backlog Grooming

When grooming the backlog, the PM Agent can:

1. Review existing stories for implicit dependencies
2. Create explicit blocker links
3. Update execution order to reflect dependencies
4. Comment on tickets explaining the dependency rationale

### Dependency Visualization

Issue links make dependencies visible in Jira:
- Developers can see what they're blocked on
- QA can understand the order to test features
- Stakeholders can see the critical path

## Architecture

### Jira Client (`tools/jira_client.py`)

Low-level functions that interact with the Jira REST API:

- `create_issue_link(inward_issue_key, outward_issue_key, link_type)`: Create a directional link
- `list_issue_links(issue_key)`: Retrieve all links for an issue

### PM Tools (`tools/pm_tools.py`)

CrewAI-compatible tool wrappers:

- `CreateBlockerLinkTool`: Wrapper for creating "blocks" links
- `ListIssueLinksToolImpl`: Wrapper for listing issue links

### PM Agent (`agents/pm_agent.py`)

Updated backstory and goal to include dependency management responsibilities.

## Link Directionality

Jira issue links are directional with "inward" and "outward" descriptions:

**Blocks Link Type:**
- **Outward**: "blocks" (this issue blocks another)
- **Inward**: "is blocked by" (this issue is blocked by another)

**Creating a Link:**
```python
create_issue_link(
    inward_issue_key="TEST-2",    # The issue being blocked
    outward_issue_key="TEST-1",   # The issue doing the blocking
    link_type="Blocks"
)
```

**Result:**
- TEST-1 → outward → "blocks TEST-2"
- TEST-2 → inward → "is blocked by TEST-1"

## Best Practices

### 1. Create Links Early
- Establish dependencies when creating stories
- Don't wait until sprint planning

### 2. Keep Links Minimal
- Only link direct dependencies
- Avoid creating transitive links (if A→B and B→C, don't also create A→C)

### 3. Sync with Execution Order
- Lower `execution_order` values for blockers
- Higher `execution_order` values for blocked stories
- Execution order should reflect the dependency graph

### 4. Review Before Duplicating
- Use `list_issue_links` before creating new links
- Avoid duplicate links between the same issues

### 5. Document Decisions
- Post a comment when creating a link explaining why
- Help the team understand the dependency reasoning

## Environment Variables

The following environment variables must be set for Jira integration:

```bash
JIRA_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=PROJ
JIRA_BOARD_ID=123
```

## Testing

Comprehensive tests are provided in:
- `uat/backend/tests/test_jira_links.py`: Tests for jira_client functions
- `uat/backend/tests/test_pm_tools.py`: Tests for PM tools

Run tests with:
```bash
pytest uat/backend/tests/test_jira_links.py -v
pytest uat/backend/tests/test_pm_tools.py -v
```

## Example PM Agent Interaction

**User Request:**
> "Create a sprint for implementing user authentication"

**PM Agent Actions:**
1. Create Epic: "User Authentication System"
2. Create Story A: "Design authentication database schema" (execution_order=1)
3. Create Story B: "Implement JWT token generation" (execution_order=2)
4. Create Story C: "Build login API endpoint" (execution_order=3)
5. Create blocker link: A blocks B
6. Create blocker link: B blocks C
7. Add all stories to sprint with appropriate goal
8. Post comments explaining the dependency chain

**Jira Result:**
- Story A shows: blocks B
- Story B shows: is blocked by A, blocks C
- Story C shows: is blocked by B
- Execution order ensures correct sequencing for the Orchestrator

## Future Enhancements

Potential improvements to consider:

1. **Remove Links**: Add tool to delete issue links
2. **Link Types**: Support other link types (Relates, Duplicates, etc.)
3. **Dependency Graph**: Generate visual dependency graphs
4. **Conflict Detection**: Warn about circular dependencies
5. **Smart Ordering**: Auto-calculate execution_order from link graph
6. **Bulk Operations**: Create multiple links in one operation

## References

- [Jira REST API - Issue Links](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-links/)
- [jira-python Library](https://jira.readthedocs.io/en/latest/)
