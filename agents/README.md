# Agents

This directory contains the AI agents that make up the virtual development team.

## Agents

### PM Agent (`pm_agent.py`)
The Project Manager Agent is responsible for:
- Reading and grooming the Jira backlog
- Creating Epics and Stories from requirements
- Estimating and prioritizing tickets
- Setting execution_order (customfield_10071) on stories
- Creating and populating sprints
- Posting status comments on issues

### Manager Agent (`manager_agent.py`)
The Manager Agent handles Jira workflow transitions with robust retry and safety features:
- Transitions Jira issues through workflow states (In Progress, Code Review, Testing, Done)
- Implements exponential backoff retry logic for API calls
- Reviews PRs with intelligent diff truncation
- **Prevents infinite retrigger loops with configurable caps**
- Manages issue assignments and status updates
- Coordinates with other agents in the system

Key features:
- **Retrigger Loop Protection**: Caps the number of times an operation can be retriggered to prevent infinite cycles
- **Exponential Backoff**: Automatic retry with exponential backoff for transient failures
- **State Tracking**: Monitors operation states and error history
- **PR Review**: Intelligent diff truncation that prioritizes new files

Configuration:
- `max_retries`: Maximum retry attempts for API calls (default: 5)
- `max_retrigger_count`: Maximum times an operation can be retriggered (default: 3)
- `base_delay`: Base delay for exponential backoff (default: 1.0s)
- `diff_max_chars`: Maximum characters for diff reviews (default: 50,000)

### Orchestrator (`orchestrator.py`)
The Sprint Orchestrator sequences and executes stories in dependency order:
- Reads tickets from a sprint
- Sorts by execution_order (customfield_10071)
- Executes tickets sequentially
- Persists state for resume capability
- Handles failures gracefully
- Provides progress tracking

## Supporting Modules

### Orchestrator State Manager (`orchestrator_state.py`)
Manages state persistence for the orchestrator:
- Create and retrieve execution states
- Checkpoint management
- Progress tracking
- State transitions

### Orchestrator CLI (`orchestrator_cli.py`)
Command-line interface for managing orchestrator executions:
- Start and resume sprints
- Monitor progress
- Pause and cancel executions
- List resumable sprints

## Usage Examples

### PM Agent
```python
from agents.pm_agent import build_pm_agent
from crewai import Crew, Task

pm_agent = build_pm_agent(verbose=True)

task = Task(
    description="Create a sprint with stories for user authentication feature",
    expected_output="Sprint created with stories, each having execution_order set",
    agent=pm_agent,
)

crew = Crew(agents=[pm_agent], tasks=[task])
result = crew.kickoff()
```

### Manager Agent
```python
from agents.manager_agent import create_manager_agent
import asyncio

# Create agent with custom retrigger limit
agent = create_manager_agent(
    max_retries=5,           # API retry attempts
    max_retrigger_count=3,   # Operation retrigger limit
    base_delay=1.0,          # Exponential backoff base
)

# Transition issue to In Progress
async def transition_issue():
    try:
        result = await agent.start_work(
            issue_key="SDT1-60",
            assignee="dev-agent",
            comment="Starting implementation",
        )
        print(f"Status: {result.status}")
        print(f"Retrigger count: {result.retrigger_count}")
    except RetriggerLimitExceeded as e:
        print(f"Retrigger limit exceeded: {e}")
        # Check operation state for debugging
        state = agent.get_operation_state("start_work", "SDT1-60")
        print(f"Operation state: {state}")

asyncio.run(transition_issue())

# Review and transition PR
async def review_pr():
    diff_text = "..."  # Git diff output
    review_result, transition_result = await agent.review_and_comment_pr(
        issue_key="SDT1-60",
        diff_text=diff_text,
    )
    print(f"New files: {len(review_result.new_files_summary)}")
    print(f"Truncated: {review_result.was_truncated}")

asyncio.run(review_pr())

# Monitor operation states
all_states = agent.get_all_operation_states()
for state in all_states:
    print(f"{state['operation_type']} on {state['issue_key']}: "
          f"{state['trigger_count']} triggers")

# Clear states (e.g., after issue resolution)
cleared = agent.clear_all_operation_states()
print(f"Cleared {cleared} operation states")
```

### Orchestrator
```python
from agents.orchestrator import Orchestrator

# Start a sprint
with Orchestrator(jira_project_key="SDT1", verbose=True) as orch:
    state_id = orch.start_sprint(
        sprint_id=123,
        sprint_name="Sprint 1",
    )

# Resume a sprint later
with Orchestrator(jira_project_key="SDT1", verbose=True) as orch:
    orch.resume_sprint(state_id)
```

### CLI
```bash
# Start a sprint
python agents/orchestrator_cli.py start \
    --sprint-id 123 \
    --sprint-name "Sprint 1" \
    --project SDT1

# Resume a sprint
python agents/orchestrator_cli.py resume \
    --state-id <uuid> \
    --project SDT1

# Check progress
python agents/orchestrator_cli.py progress \
    --state-id <uuid> \
    --project SDT1

# List resumable sprints
python agents/orchestrator_cli.py list --project SDT1
```

## Integration Flow

```
1. PM Agent creates sprint with stories
   └─> Sets execution_order on each story
   
2. Orchestrator starts sprint execution
   └─> Fetches stories sorted by execution_order
   └─> Creates OrchestratorState in database
   └─> Begins sequential execution
   
3. For each story:
   └─> Dev Agent implements the story
   └─> Manager Agent transitions to Code Review
   └─> QA Agent tests the implementation
   └─> Manager Agent transitions to Done
   └─> Checkpoints state
   └─> Handles failures with retrigger limits
   
4. If interrupted:
   └─> State persisted in database
   └─> Can resume from last checkpoint
   └─> Skips completed tickets
   
5. Completion:
   └─> Marks state as COMPLETED
   └─> Reports summary
```

## Manager Agent Retrigger Loop Protection

The Manager Agent includes built-in protection against infinite retrigger loops:

### How It Works
1. **Operation Tracking**: Each operation (start_work, complete_work, move_to_code_review, etc.) is tracked by operation type and issue key
2. **Trigger Counting**: Every invocation increments a trigger counter
3. **Limit Enforcement**: When the counter reaches `max_retrigger_count`, a `RetriggerLimitExceeded` exception is raised
4. **Auto-Reset on Success**: Successful operations reset their trigger count
5. **Error History**: Failed operations record error messages for debugging

### Why This Matters
- Prevents infinite loops in workflow automation
- Protects against misconfigured workflows that continuously retrigger
- Provides clear error messages when limits are exceeded
- Tracks operation history for debugging
- Allows different operations on the same issue to proceed independently

### Configuration
```python
# Default: 3 retriggers before raising exception
agent = create_manager_agent(max_retrigger_count=3)

# Custom limit for high-reliability scenarios
agent = create_manager_agent(max_retrigger_count=5)

# More aggressive limit for testing
agent = create_manager_agent(max_retrigger_count=1)
```

### Monitoring
```python
# Check specific operation state
state = agent.get_operation_state("start_work", "SDT1-60")
print(f"Triggers: {state['trigger_count']}")
print(f"Recent errors: {state['recent_errors']}")

# Monitor all operations
for state in agent.get_all_operation_states():
    if state['trigger_count'] >= 2:
        print(f"Warning: {state['operation_id']} approaching limit")

# Clear states after resolving issues
agent.clear_all_operation_states()
```

### Example Scenario
```
1. Orchestrator calls manager_agent.start_work("SDT1-60")
   → Trigger count: 1 → Success → Count reset

2. Network issue causes retry loop:
   → manager_agent.move_to_code_review("SDT1-60") → Fails → Count: 1
   → Orchestrator retriggers → Fails → Count: 2
   → Orchestrator retriggers → Fails → Count: 3
   → Orchestrator retriggers → RetriggerLimitExceeded raised
   
3. Orchestrator catches exception, logs issue, moves to next ticket

4. Manual intervention resolves issue:
   → agent.clear_all_operation_states()
   → manager_agent.move_to_code_review("SDT1-60") → Success
```

## Dependencies

- `crewai` - AI agent framework
- `sqlalchemy` - Database ORM
- `psycopg2-binary` - PostgreSQL driver
- `pydantic` - Data validation
- `httpx` - HTTP client for Jira API (Manager Agent)

## Configuration

Environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `ANTHROPIC_API_KEY` - Claude API key for PM Agent
- `JIRA_BASE_URL` - Jira instance URL
- `JIRA_EMAIL` - Jira user email
- `JIRA_API_TOKEN` - Jira API token
- `JIRA_PROJECT_KEY` - Jira project key (e.g., "SDT1")

## Testing

Run tests:
```bash
# Orchestrator tests
cd uat/backend
pytest tests/test_orchestrator.py -v
pytest tests/test_orchestrator_state.py -v

# Manager Agent tests
cd agents
pytest tests/test_manager_agent.py -v

# Run specific test classes
pytest tests/test_manager_agent.py::TestManagerAgentRetrigger -v
pytest tests/test_manager_agent.py::TestOperationState -v
```

## Documentation

See `docs/orchestrator_resume_capability.md` for detailed documentation on:
- Architecture and design
- State persistence
- Resume capability
- Error handling
- Best practices
- Troubleshooting

## Future Agents

Planned agents for the virtual dev team:
- Dev Agent - Implements stories (already exists)
- QA Agent - Tests implementations
- DevOps Agent - Handles deployments
- Security Agent - Performs security reviews
- Code Review Agent - Reviews pull requests
