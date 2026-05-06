# SDT1-73: PM Agent Starts Jira Sprint on Approval

## Overview

This feature enables the PM Agent to start (activate) Jira sprints programmatically through the `start_sprint` tool. Once a sprint is planned, populated with stories, and ready for execution, the PM Agent can transition it from 'future' state to 'active' state, signaling the development team to begin work.

## Implementation

### Core Functionality

#### 1. `jira_client.start_sprint(sprint_id: int)`

Low-level function that interfaces with the Jira API to activate a sprint.

**Location:** `tools/jira_client.py`

**Parameters:**
- `sprint_id` (int): The numeric ID of the sprint to start

**Returns:**
```python
{
    "id": int,
    "name": str,
    "state": str,  # Should be "active"
    "start_date": str,  # ISO-8601 format
    "end_date": str,    # ISO-8601 format
    "goal": str
}
```

**Validation:**
- Sprint must be in 'future' state (not 'active' or 'closed')
- Sprint must have `start_date` and `end_date` configured
- Only one sprint can be active per board at a time

**Error Handling:**
- Raises `ValueError` if sprint is not in 'future' state
- Raises `ValueError` if sprint lacks required dates
- Raises `Exception` for Jira API errors

#### 2. `StartSprintTool`

CrewAI tool wrapper that makes `start_sprint` available to the PM Agent.

**Location:** `tools/pm_tools.py`

**Tool Name:** `start_sprint`

**Description:** Start (activate) a sprint by its ID. This transitions the sprint from 'future' state to 'active' state.

**Input Schema:**
```python
{
    "sprint_id": int  # Required
}
```

**Output:** Formatted string with sprint details or error message

**Features:**
- Gracefully handles errors (ValueError, generic exceptions)
- Returns human-readable success/error messages
- Handles missing optional fields (goal, dates)

### PM Agent Integration

#### Updated Responsibilities

The PM Agent backstory now includes sprint start as a core responsibility:

> **6. SPRINT START** — Once a sprint is populated and ready, start it using the
> start_sprint tool. This activates the sprint and signals the team to begin work.
> Only start a sprint after:
> - All stories are added to the sprint
> - All execution_order values are set correctly
> - All dependencies are documented with issue links
> - The sprint has start_date and end_date configured

#### Tool Availability

The `StartSprintTool` is included in the `SPRINT_TOOLS` group and is available to the PM Agent when using `ALL_PM_TOOLS` or `SPRINT_TOOLS`.

### Workflow

The typical sprint planning workflow now includes:

1. **Create Sprint** → `create_sprint(name, goal, start_date, end_date)`
2. **Create Stories** → `create_story(...)` for each story
3. **Set Dependencies** → `create_blocker_link(...)` where needed
4. **Add to Sprint** → `add_issues_to_sprint(sprint_id, issue_keys)`
5. **Start Sprint** → `start_sprint(sprint_id)` ✨ **NEW**

## Usage Examples

### Example 1: Basic Sprint Start

```python
from tools import jira_client

# Sprint 123 already exists in 'future' state with dates configured
result = jira_client.start_sprint(123)

print(f"Sprint {result['name']} is now {result['state']}")
# Output: Sprint "Sprint 1" is now active
```

### Example 2: Using the PM Agent Tool

```python
from tools.pm_tools import StartSprintTool

tool = StartSprintTool()
result = tool._run(sprint_id=123)

print(result)
# Output:
# Sprint started successfully!
#   ID: 123
#   Name: Sprint 1
#   State: active
#   Start: 2025-01-20T09:00:00.000Z
#   End: 2025-02-03T17:00:00.000Z
```

### Example 3: Error Handling

```python
from tools import jira_client

# Attempting to start a sprint that's already active
try:
    result = jira_client.start_sprint(123)
except ValueError as e:
    print(f"Cannot start sprint: {e}")
    # Output: Cannot start sprint: Sprint 123 is in 'active' state. 
    #         Only sprints in 'future' state can be started.
```

### Example 4: Complete Workflow

```python
from tools import jira_client

# 1. Create a sprint
sprint = jira_client.create_sprint(
    name="Sprint 1",
    goal="Implement authentication",
    start_date="2025-01-20T09:00:00.000Z",
    end_date="2025-02-03T17:00:00.000Z"
)

sprint_id = sprint["id"]
print(f"Created sprint {sprint_id}: {sprint['name']}")

# 2. Add issues to the sprint
issue_keys = ["SDT1-1", "SDT1-2", "SDT1-3"]
jira_client.add_issues_to_sprint(sprint_id, issue_keys)
print(f"Added {len(issue_keys)} issues to sprint")

# 3. Start the sprint
result = jira_client.start_sprint(sprint_id)
print(f"Sprint {result['name']} started! State: {result['state']}")
```

## Testing

### Unit Tests

#### Test File 1: `tools/tests/test_jira_client_start_sprint.py`

Tests the core `start_sprint` function:
- ✅ Successfully starting a sprint in 'future' state
- ✅ Error when sprint is already active
- ✅ Error when sprint is in 'closed' state
- ✅ Error when start_date is missing
- ✅ Error when end_date is missing
- ✅ Handling sprints without optional attributes (goal)
- ✅ Integration with create_sprint workflow

#### Test File 2: `tools/tests/test_pm_tools_start_sprint.py`

Tests the `StartSprintTool` wrapper:
- ✅ Successful sprint start with tool
- ✅ ValueError handling
- ✅ Generic exception handling
- ✅ Missing dates error handling
- ✅ Minimal response data handling
- ✅ Tool metadata verification
- ✅ Input schema validation
- ✅ Tool inclusion in SPRINT_TOOLS
- ✅ Complete workflow simulation

### Running Tests

```bash
# Run all start_sprint tests
pytest tools/tests/test_jira_client_start_sprint.py -v
pytest tools/tests/test_pm_tools_start_sprint.py -v

# Run with coverage
pytest tools/tests/test_*_start_sprint.py --cov=tools --cov-report=html
```

## API Changes

### New Function: `jira_client.start_sprint`

```python
def start_sprint(sprint_id: int) -> dict[str, Any]:
    """Start (activate) a sprint by its ID.
    
    Transitions a sprint from 'future' state to 'active' state.
    
    Args:
        sprint_id: The numeric ID of the sprint to start
    
    Returns:
        A dictionary containing:
            - id: The sprint ID
            - name: The sprint name
            - state: The new sprint state (should be 'active')
            - start_date: The sprint start date (ISO-8601)
            - end_date: The sprint end date (ISO-8601)
            - goal: The sprint goal
    
    Raises:
        ValueError: If the sprint is not in 'future' state or if 
                   required dates are missing
        Exception: If the Jira API call fails
    """
```

### New Tool: `StartSprintTool`

```python
class StartSprintTool(BaseTool):
    name: str = "start_sprint"
    description: str = (
        "Start (activate) a sprint by its ID. This transitions the sprint "
        "from 'future' state to 'active' state. Use this after creating a "
        "sprint and adding issues to it, once the team is ready to begin work."
    )
    args_schema: type = StartSprintInput

    def _run(self, sprint_id: int) -> str:
        """Execute the tool."""
```

## Configuration

No new environment variables required. Uses existing Jira configuration:
- `JIRA_URL`
- `JIRA_EMAIL`
- `JIRA_API_TOKEN`
- `JIRA_PROJECT_KEY`
- `JIRA_BOARD_ID`

## Dependencies

Added to `requirements.txt`:
- `jira==3.5.2` (Python Jira library)

## Future Enhancements

Potential improvements for future tickets:

1. **Auto-Start on Approval**: Integrate with approval workflow to automatically start sprints when approved
2. **Pre-Start Validation**: Add comprehensive pre-start checks (all stories have execution_order, no missing dependencies, etc.)
3. **Sprint Metrics**: Track sprint start times, velocity, and completion rates
4. **Notification**: Send notifications to team members when a sprint starts
5. **Sprint Health Check**: Validate sprint health before starting (balanced workload, clear goals, etc.)

## Migration Notes

This is a purely additive change:
- ✅ No breaking changes to existing APIs
- ✅ Backward compatible with existing PM Agent workflows
- ✅ Existing sprints are not affected
- ✅ Existing tools continue to work as before

## References

- **Ticket**: SDT1-73
- **Jira API**: [Sprint REST API Documentation](https://developer.atlassian.com/cloud/jira/software/rest/api-group-sprint/)
- **Related Tickets**: 
  - SDT1-47: Router refactoring (established patterns)
  - SDT1-63: JWT validation (security patterns)
  - Previous sprint management features

## Rollback Plan

If issues are discovered:

1. Remove `StartSprintTool` from `SPRINT_TOOLS` in `tools/pm_tools.py`
2. Revert changes to PM Agent backstory
3. Remove `start_sprint` function from `tools/jira_client.py`
4. Sprints can still be started manually in Jira UI

No database migrations or data changes required for rollback.
