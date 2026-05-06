# Sprint Starting Guide

## Overview

This guide explains how the PM Agent can start Jira sprints upon approval, transitioning them from a planning state to active execution.

## Feature: Sprint Starting

### Purpose

The sprint starting feature enables the PM Agent to activate a sprint in Jira once it has been approved and is ready for execution. This transitions the sprint from a `future` state to an `active` state, signaling to the development team that work can begin immediately.

### When to Use

The PM Agent should start a sprint when:

1. **Explicit Approval**: A stakeholder or team lead explicitly approves the sprint to begin
2. **Sprint Planning Complete**: All stories have been added, estimated, and have execution_order set
3. **Dependencies Clear**: All blocking relationships are documented via issue links
4. **Team Ready**: The development team is prepared to begin work

### How It Works

#### 1. Sprint Creation Workflow

```python
# Step 1: Create the sprint
create_sprint(
    name="Sprint 1",
    goal="Complete authentication features",
    start_date="2025-05-01T09:00:00.000Z",
    end_date="2025-05-15T09:00:00.000Z"
)
# Returns: Sprint ID (e.g., 123)

# Step 2: Add issues to the sprint
add_issues_to_sprint(
    sprint_id=123,
    issue_keys=["SDT1-1", "SDT1-2", "SDT1-3"]
)

# Step 3: Verify and approve (manual or automated check)

# Step 4: Start the sprint
start_sprint(sprint_id=123)
# Transitions sprint from 'future' to 'active'
```

#### 2. API Details

**Function Signature:**
```python
def start_sprint(sprint_id: int) -> dict[str, Any]:
    """Start a sprint, transitioning it from 'future' to 'active' state.
    
    Args:
        sprint_id: The ID of the sprint to start
    
    Returns:
        Dictionary with sprint details including id, name, state, dates
    
    Raises:
        ValueError: If sprint is already active or closed
    """
```

**Tool Wrapper:**
```python
class StartSprintTool(BaseTool):
    name: "start_sprint"
    description: "Start a sprint, transitioning it from 'future' to 'active' state."
```

### PM Agent Integration

The PM Agent includes sprint starting capability in its responsibilities:

```
6. SPRINT ACTIVATION — Once a sprint is approved (by stakeholders or explicitly
   requested), start the sprint using start_sprint to transition it from 'future'
   to 'active' state. This signals to the team that work can begin immediately.
```

**Agent Goal:**
> "...plan and populate sprints; start sprints upon approval so the development 
> team can begin work immediately."

### Error Handling

The sprint starting functionality handles several error cases:

1. **Already Active**: Cannot start a sprint that is already active
   ```
   ValueError: Sprint 123 is already active
   ```

2. **Closed Sprint**: Cannot restart a closed sprint
   ```
   ValueError: Sprint 123 is closed and cannot be started
   ```

3. **No Issues**: Some Jira instances may require sprints to have at least one issue
   ```
   ValueError: Failed to start sprint 123: Bad request: sprint has no issues
   ```

4. **API Errors**: Network or permission issues are caught and reported
   ```
   ValueError: Failed to start sprint 123: 403 - Insufficient permissions
   ```

### Best Practices

1. **Pre-Start Checklist**:
   - ✅ All stories have execution_order set
   - ✅ All stories are linked to epics
   - ✅ All dependencies are documented with issue links
   - ✅ Sprint has at least one story
   - ✅ Sprint goal is clear and actionable
   - ✅ Start and end dates are set appropriately

2. **Communication**:
   - Post a comment on the sprint's main epic when starting
   - Notify the team via Jira notifications
   - Document the sprint's readiness state before starting

3. **Validation**:
   - Use `list_sprints()` to verify the sprint exists and is in 'future' state
   - Check that all issues in the sprint have execution_order
   - Verify no blocking issues are in other sprints

4. **Never Auto-Start**:
   - Always wait for explicit approval or request
   - Don't start sprints automatically in response to sprint creation
   - Maintain human oversight in the sprint activation decision

### Example Usage

#### Complete Workflow Example

```python
from tools.pm_tools import (
    CreateSprintTool,
    AddToSprintTool,
    StartSprintTool,
    AddCommentTool,
)

# 1. Create sprint
create_tool = CreateSprintTool()
result = create_tool._run(
    name="Sprint 5 - Authentication",
    goal="Implement user authentication and session management",
    start_date="2025-05-01T09:00:00.000Z",
    end_date="2025-05-15T09:00:00.000Z"
)
# Output: "Sprint created: ID=125 — Sprint 5 - Authentication"

# 2. Add pre-planned stories
add_tool = AddToSprintTool()
add_tool._run(
    sprint_id=125,
    issue_keys=[
        "SDT1-45",  # Login UI (execution_order: 1)
        "SDT1-46",  # JWT implementation (execution_order: 2)
        "SDT1-47",  # Session store (execution_order: 3)
        "SDT1-48",  # Logout flow (execution_order: 4)
    ]
)

# 3. Post planning comment
comment_tool = AddCommentTool()
comment_tool._run(
    issue_key="SDT1-45",  # Epic or first story
    body="Sprint 5 planned and ready for approval. Total: 21 story points across 4 stories."
)

# 4. Wait for approval (manual step or automated approval logic)

# 5. Start sprint
start_tool = StartSprintTool()
result = start_tool._run(sprint_id=125)
# Output: "✓ Sprint started successfully: Sprint 5 - Authentication (ID: 125) — State: active"

# 6. Post start notification
comment_tool._run(
    issue_key="SDT1-45",
    body="Sprint 5 is now ACTIVE. Development team can begin work."
)
```

### Integration with Orchestrator

Once a sprint is started, the Orchestrator can automatically:

1. Fetch all stories in the active sprint
2. Sort by execution_order
3. Begin sequential execution
4. Track progress in the database

The sprint must be in `active` state for the Orchestrator to process it:

```python
from agents.orchestrator import start_sprint_execution

# After PM Agent starts the sprint
state_id = start_sprint_execution(
    sprint_id=125,
    sprint_name="Sprint 5 - Authentication",
    jira_project_key="SDT1",
    verbose=True
)
```

### Testing

Run the test suite to verify sprint starting functionality:

```bash
pytest tools/tests/test_jira_sprint_start.py -v
```

**Test Coverage:**
- ✅ Successful sprint start
- ✅ Already active sprint error
- ✅ Closed sprint error
- ✅ API error handling
- ✅ Minimal fields handling
- ✅ Tool wrapper success
- ✅ Tool wrapper error handling
- ✅ Complete workflow integration

### Environment Configuration

Required environment variables:

```bash
# Jira connection
JIRA_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token

# Project configuration
JIRA_PROJECT_KEY=SDT1
JIRA_BOARD_ID=1
```

### API Reference

#### `start_sprint(sprint_id: int) -> dict`

**Parameters:**
- `sprint_id` (int): The ID of the sprint to start

**Returns:**
- `dict`: Sprint details including:
  - `id` (int): Sprint ID
  - `name` (str): Sprint name
  - `state` (str): Sprint state (should be 'active')
  - `start_date` (str | None): ISO-8601 start date
  - `end_date` (str | None): ISO-8601 end date
  - `goal` (str): Sprint goal

**Raises:**
- `ValueError`: If sprint is already active, closed, or cannot be started

**Example:**
```python
from tools.jira_client import start_sprint

result = start_sprint(123)
print(f"Sprint {result['name']} is now {result['state']}")
# Output: Sprint Sprint 1 is now active
```

### Troubleshooting

**Issue: Sprint won't start**

Possible causes:
1. Sprint has no issues → Add at least one story
2. Sprint already active → Check sprint state with `list_sprints()`
3. Insufficient permissions → Verify API token has sprint management rights
4. Sprint dates invalid → Ensure start_date < end_date

**Issue: Tool returns success but sprint still in 'future' state**

1. Check Jira workflow restrictions in board settings
2. Verify board configuration allows sprint activation
3. Check for conflicting active sprints on the same board

### Future Enhancements

Potential improvements for this feature:

1. **Automatic Validation**: Pre-flight checks before starting
2. **Approval Workflow**: Integration with approval systems
3. **Notifications**: Automatic team notifications on sprint start
4. **Rollback**: Ability to transition sprint back to 'future' state
5. **Metrics**: Track sprint start patterns and timing
6. **Webhooks**: Trigger external systems when sprint starts

### Related Documentation

- [PM Agent Guide](../agents/pm_agent.py)
- [Sprint Planning Workflow](./sprint-planning.md)
- [Orchestrator Documentation](../agents/orchestrator.py)
- [Jira Client API](../tools/jira_client.py)
