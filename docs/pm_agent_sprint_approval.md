# PM Agent Sprint Approval and Start

## Overview

The PM Agent can now start Jira sprints after they have been created and populated with stories. This feature enables a complete sprint planning workflow:

1. **Plan**: PM Agent creates sprint and adds stories
2. **Review**: Human reviews the sprint plan
3. **Approve**: Human gives approval to start
4. **Start**: PM Agent activates the sprint in Jira

## Feature Details

### New Capability: `start_sprint` Tool

The PM Agent now has access to the `start_sprint` tool, which activates a sprint that is currently in "future" state.

**Parameters:**
- `sprint_id` (int): The ID of the sprint to start

**Returns:**
- Sprint details including ID, name, state (now "active"), start date, and end date

**Constraints:**
- Only sprints in "future" state can be started
- Active or closed sprints cannot be restarted
- The sprint must already have been created in Jira

### Workflow Example

#### 1. Create and Populate Sprint

```python
from crewai import Crew, Task
from agents.pm_agent import build_pm_agent
from tools.pm_tools import ALL_PM_TOOLS

# Build PM Agent with all tools
pm_agent = build_pm_agent(tools=ALL_PM_TOOLS)

# Task to create and populate sprint
planning_task = Task(
    description="""
    Create a new 2-week sprint called 'Sprint 15' starting tomorrow.
    Add the following stories from the backlog:
    - SDT1-101
    - SDT1-102
    - SDT1-103
    
    Set a sprint goal: 'Complete user authentication feature'
    """,
    agent=pm_agent,
    expected_output="Sprint created and populated with stories"
)

# Execute
crew = Crew(agents=[pm_agent], tasks=[planning_task])
result = crew.kickoff()
```

#### 2. Review Sprint Plan

After the sprint is created, review it in Jira or through the PM Agent:

```python
# Task to review sprint
review_task = Task(
    description="""
    List all sprints and show the details of Sprint 15.
    Confirm it has the correct stories and sprint goal.
    """,
    agent=pm_agent,
    expected_output="Sprint details confirmed"
)
```

#### 3. Start Sprint on Approval

Once approved, start the sprint:

```python
# Task to start sprint
start_task = Task(
    description="""
    Start Sprint 15 (ID: 42) now that it has been approved.
    Confirm the sprint is now active.
    """,
    agent=pm_agent,
    expected_output="Sprint started successfully"
)
```

### Direct API Usage

You can also use the functionality directly:

```python
from tools.jira_client import start_sprint

# Start sprint by ID
result = start_sprint(sprint_id=42)

print(f"Sprint {result['name']} is now {result['state']}")
# Output: Sprint Sprint 15 is now active
```

### Error Handling

The tool handles various error scenarios gracefully:

**Sprint Not in Future State:**
```python
# Trying to start an already active sprint
result = tool._run(sprint_id=123)
# Returns: "Error starting sprint: Cannot start sprint 123 with state 'active'. 
#           Only sprints in 'future' state can be started."
```

**API Errors:**
```python
# API communication failure
# Returns: "Unexpected error starting sprint: Network timeout"
```

## PM Agent Capabilities

The PM Agent's backstory has been updated to include:

### 6. SPRINT ACTIVATION

> After creating and populating a sprint, start it using the start_sprint tool 
> when you receive approval or when ready to begin work. Only sprints in 'future' 
> state can be started. Starting a sprint activates it and begins the sprint timeline.

### Updated Rules

> - After creating and populating a sprint, use start_sprint to activate it when approved.
> - Only start sprints that are in 'future' state — active or completed sprints cannot be restarted.

## Integration with Orchestrator

Once a sprint is started:

1. Stories are in "To Do" status
2. Orchestrator can fetch sprint tickets using execution_order
3. Development workflow begins automatically

The sprint start action is the trigger that makes a sprint ready for the Orchestrator to process.

## Testing

Comprehensive tests are included:

- **Unit tests**: `tools/tests/test_start_sprint.py`
  - Tests for `jira_client.start_sprint()` function
  - Tests for `StartSprintTool` wrapper
  - Error handling scenarios
  
- **Integration tests**: `agents/tests/test_pm_agent_start_sprint.py`
  - PM Agent has access to the tool
  - Backstory includes instructions
  - Complete workflow validation

Run tests:
```bash
pytest tools/tests/test_start_sprint.py -v
pytest agents/tests/test_pm_agent_start_sprint.py -v
```

## API Reference

### `jira_client.start_sprint(sprint_id: int)`

Start a sprint that is in 'future' state.

**Parameters:**
- `sprint_id` (int): The ID of the sprint to start

**Returns:**
- `dict`: Sprint information
  - `id` (int): Sprint ID
  - `name` (str): Sprint name
  - `state` (str): Sprint state (should be "active")
  - `start_date` (str): ISO-8601 start date
  - `end_date` (str): ISO-8601 end date

**Raises:**
- `ValueError`: If sprint is not in 'future' state or API call fails

### `StartSprintTool._run(sprint_id: int)`

CrewAI tool wrapper for starting sprints.

**Parameters:**
- `sprint_id` (int): The ID of the sprint to start

**Returns:**
- `str`: Success message with sprint details, or error message

## Common Use Cases

### 1. Automated Sprint Start After Planning

```python
task = Task(
    description="""
    Create Sprint 20 for next iteration.
    Add top-priority stories from backlog (aim for 30 story points).
    Once populated, start the sprint immediately.
    """,
    agent=pm_agent,
    expected_output="Sprint created, populated, and started"
)
```

### 2. Conditional Sprint Start

```python
task = Task(
    description="""
    Review Sprint 21 and verify:
    - All stories have execution_order set
    - Total story points are between 20-40
    - All stories have acceptance criteria
    
    If all checks pass, start the sprint.
    Otherwise, report what needs to be fixed.
    """,
    agent=pm_agent,
    expected_output="Sprint validation and start result"
)
```

### 3. Sprint Coordination with Team

```python
task = Task(
    description="""
    Sprint 22 has been reviewed and approved by the team in today's planning meeting.
    Start Sprint 22 (ID: 156) and post a comment on each story confirming 
    the sprint is now active and ready for development.
    """,
    agent=pm_agent,
    expected_output="Sprint started and team notified"
)
```

## Best Practices

1. **Always Review Before Starting**
   - Verify all stories have execution_order set
   - Check story points total is reasonable
   - Ensure sprint dates are correct

2. **Document Sprint Start**
   - Post a comment on the sprint or stories when starting
   - Include sprint goal and key objectives
   - Notify the team through appropriate channels

3. **Error Recovery**
   - If start fails, check sprint state in Jira
   - Verify sprint has stories assigned
   - Ensure dates are properly configured

4. **Workflow Integration**
   - Start sprint only after human approval
   - Coordinate with Orchestrator launch
   - Align with team ceremonies (stand-up, planning)

## Troubleshooting

### "Cannot start sprint with state 'active'"

**Cause**: Sprint is already active
**Solution**: Check sprint status in Jira. You may need to create a new sprint.

### "Cannot start sprint with state 'closed'"

**Cause**: Sprint has been completed
**Solution**: Create a new sprint for the next iteration.

### "Failed to start sprint: Status 400"

**Cause**: API validation error (missing dates, no stories, etc.)
**Solution**: 
- Ensure sprint has start and end dates
- Verify sprint has at least one story
- Check sprint configuration in Jira

### Sprint starts but Orchestrator doesn't pick it up

**Cause**: Stories missing execution_order
**Solution**: PM Agent must set execution_order on all stories before starting sprint.

## Related Documentation

- [PM Agent Overview](pm_agent.md)
- [Sprint Management](sprint_management.md)
- [Orchestrator Integration](orchestrator.md)
- [Jira Custom Fields](jira_custom_fields.md)
