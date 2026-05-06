# PM Agent Sprint Start Workflow (SDT1-73)

## Overview

The PM Agent can now start (activate) Jira sprints on approval, enabling a complete end-to-end workflow from sprint planning to execution.

## Workflow

### 1. Sprint Planning Phase

The PM Agent creates and populates a sprint:

```python
# Create a sprint
create_sprint(name="Sprint 1", goal="Implement user authentication")

# Add stories to the sprint
add_issues_to_sprint(sprint_id=123, issue_keys=["SDT1-45", "SDT1-46", "SDT1-47"])
```

At this stage, the sprint is in **"future"** state in Jira.

### 2. Approval Phase

The PM Agent presents the sprint plan to the product owner or stakeholder for review and approval. The agent should:

1. List the sprint contents (stories, estimates, execution order)
2. Explain the sprint goal and expected deliverables
3. Highlight any risks or dependencies
4. Request explicit approval to start the sprint

### 3. Sprint Activation Phase

Once approval is received, the PM Agent uses the `start_sprint` tool:

```python
start_sprint(sprint_id=123)
```

This transitions the sprint from **"future"** to **"active"** state in Jira, signaling to the development team that work can begin.

## Tool: `start_sprint`

### Usage

```python
from tools.pm_tools import StartSprintTool

tool = StartSprintTool()
result = tool._run(sprint_id=123)
```

### Parameters

- `sprint_id` (int, required): The ID of the sprint to start

### Returns

Success message with sprint details:
```
✓ Sprint started successfully!
  Sprint ID: 123
  Name: Sprint 1
  State: active
  Goal: Implement user authentication
```

Error message if the sprint cannot be started:
```
✗ Failed to start sprint: Sprint 123 is already active
```

### Error Handling

The tool handles several error conditions:

1. **Sprint already active**: Returns an error message indicating the sprint is already running
2. **Sprint closed**: Returns an error indicating closed sprints cannot be restarted
3. **API errors**: Catches and reports Jira API connection or authentication errors

## PM Agent Integration

### Agent Capabilities

The PM Agent has been updated with:

1. **New tool**: `start_sprint` added to `SPRINT_TOOLS` and `ALL_PM_TOOLS`
2. **Updated backstory**: Includes guidance on sprint activation workflow
3. **Updated goal**: Explicitly mentions starting approved sprints

### Agent Instructions

The PM Agent follows these guidelines for sprint activation:

- **Never start a sprint without explicit approval** from the user
- **Verify all stories have execution_order set** before starting
- **Confirm the sprint state** is 'future' before attempting to start
- **Report success or failure** clearly to the user

## Jira Client Implementation

### Function: `jira_client.start_sprint`

```python
def start_sprint(sprint_id: int) -> dict[str, Any]:
    """Start (activate) a sprint in Jira.
    
    This transitions a sprint from 'future' state to 'active' state,
    making it the current working sprint for the team.
    
    Args:
        sprint_id: The ID of the sprint to start
    
    Returns:
        A dictionary containing:
            - id: The sprint ID
            - name: The sprint name
            - state: The sprint state (should be 'active' after starting)
            - start_date: The start date
            - end_date: The end date
    
    Raises:
        ValueError: If the sprint is already active or closed
        Exception: If the Jira API call fails
    """
```

### Implementation Details

1. **State validation**: Checks current sprint state before attempting update
2. **API call**: Uses `jira.update_sprint(sprint_id, state="active")`
3. **State refresh**: Fetches updated sprint to confirm state change
4. **Error handling**: Provides clear error messages for invalid states

## Example Conversation Flow

**User**: "Can you create a sprint for the authentication feature?"

**PM Agent**: "I'll create a sprint with the authentication stories. Let me review the backlog first."

*[PM Agent creates sprint, adds stories]*

**PM Agent**: "I've created Sprint 1 with 5 stories totaling 21 story points:
- SDT1-45: Implement login API (5 pts, order: 1)
- SDT1-46: Add JWT authentication (8 pts, order: 2)
- SDT1-47: Create user registration (5 pts, order: 3)
- SDT1-48: Password reset flow (3 pts, order: 4)

All stories have execution order set and dependencies are documented. Should I start this sprint?"

**User**: "Yes, please start it."

**PM Agent**: "Starting Sprint 1..."

*[PM Agent calls start_sprint(123)]*

**PM Agent**: "✓ Sprint 1 has been started and is now active! The development team can begin work on SDT1-45 (Implement login API)."

## Integration with Orchestrator

Once a sprint is started (active), it can be picked up by the Orchestrator for automated execution:

```python
from agents.orchestrator import start_sprint_execution

state_id = start_sprint_execution(
    sprint_id=123,
    sprint_name="Sprint 1",
    jira_project_key="SDT1"
)
```

The Orchestrator will:
1. Fetch all "To Do" stories from the sprint
2. Order them by execution_order (customfield_10071)
3. Execute them sequentially
4. Track progress and handle failures

## Testing

Comprehensive tests are included in `uat/backend/tests/test_pm_sprint_start.py`:

- `TestJiraClientStartSprint`: Unit tests for the Jira client function
- `TestStartSprintTool`: Tests for the CrewAI tool wrapper
- `TestPMAgentSprintWorkflow`: Integration tests for the PM Agent workflow
- `TestSprintStartValidation`: Tests for validation and error handling

Run tests with:
```bash
pytest uat/backend/tests/test_pm_sprint_start.py -v
```

## Environment Variables

Ensure the following environment variables are set:

- `JIRA_URL`: Jira instance URL (e.g., "https://yourcompany.atlassian.net")
- `JIRA_EMAIL`: Jira user email
- `JIRA_API_TOKEN`: Jira API token
- `JIRA_PROJECT_KEY`: Project key (e.g., "SDT1")
- `JIRA_BOARD_ID`: Board ID for the project

## Best Practices

1. **Always verify sprint contents** before starting
2. **Check execution_order** on all stories
3. **Document the sprint goal** clearly
4. **Get explicit approval** before activation
5. **Confirm state change** after starting
6. **Log the action** for audit purposes

## Troubleshooting

### Sprint won't start

**Problem**: `start_sprint` fails with "Sprint is already active"

**Solution**: Check sprint state with `list_sprints` to verify current state

### Permission denied

**Problem**: API returns 403 Forbidden

**Solution**: Verify Jira API token has permission to update sprints

### Sprint not found

**Problem**: API returns 404 Not Found

**Solution**: Verify sprint ID is correct using `list_sprints`

## References

- Jira Sprint API: https://developer.atlassian.com/cloud/jira/software/rest/api-group-sprint/
- CrewAI Tools: https://docs.crewai.com/core-concepts/Tools/
- PM Agent: `agents/pm_agent.py`
- Orchestrator: `agents/orchestrator.py`
