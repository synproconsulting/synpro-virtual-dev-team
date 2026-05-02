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

### Orchestrator (`orchestrator.py`)
The Sprint Orchestrator sequences and executes stories in dependency order:
- Reads tickets from a sprint
- Sorts by execution_order (customfield_10071)
- Executes tickets sequentially
- Persists state for resume capability
- Handles failures gracefully
- Provides progress tracking

### Cap Manager Agent (`cap_manager_agent.py`)
The Capacity Manager Agent manages capacity planning and prevents infinite retrigger loops:
- **Retrigger Loop Protection**: Prevents infinite cycles by capping the number of retrigger attempts per ticket
- **Configurable Limits**: Customize max attempts and time windows via environment variables or initialization parameters
- **Time Window Reset**: Automatically resets retrigger counts after a configurable time window
- **Detailed Tracking**: Maintains complete history of retrigger attempts with timestamps and reasons
- **Manual Reset**: Allows manual reset of retrigger state when needed

#### Features

- **Retrigger Loop Protection**: Prevents infinite cycles by capping the number of retrigger attempts per ticket
- **Configurable Limits**: Customize max attempts and time windows via environment variables or initialization parameters
- **Time Window Reset**: Automatically resets retrigger counts after a configurable time window
- **Detailed Tracking**: Maintains complete history of retrigger attempts with timestamps and reasons
- **Manual Reset**: Allows manual reset of retrigger state when needed

#### Configuration

Environment variables:
- `MAX_RETRIGGER_ATTEMPTS`: Maximum number of retrigger attempts per ticket (default: 3)
- `RETRIGGER_WINDOW_MINUTES`: Time window in minutes for counting retriggers (default: 60)

#### Usage

```python
from agents.cap_manager_agent import CapManagerAgent

# Initialize with defaults
agent = CapManagerAgent()

# Or with custom configuration
agent = CapManagerAgent(
    max_retrigger_attempts=5,
    retrigger_window_minutes=120
)

# Check if a ticket can be retriggered
if agent.can_retrigger("STORY-123", "dependency resolved"):
    agent.record_retrigger("STORY-123", "dependency resolved")
    # ... perform retrigger logic

# Or use the unified interface
result = agent.manage_capacity(
    ticket_id="STORY-123",
    action="retrigger",
    context={"reason": "capacity available"}
)

if result["success"]:
    print(f"Retrigger successful: {result}")
else:
    print(f"Retrigger blocked: {result['error']}")
```

#### Actions

The `manage_capacity()` method supports the following actions:

- **`retrigger`**: Attempt to retrigger a ticket (checks limit and records attempt)
- **`check`**: Check if a ticket can be retriggered without recording an attempt
- **`reset`**: Reset the retrigger state for a ticket
- **`query`**: Get the current retrigger state for a ticket

#### Integration

See `agents/examples/orchestrator_integration.py` for a complete example of integrating the Cap Manager Agent into the orchestrator's ticket processing pipeline.

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

### Retrigger Monitoring (`monitoring.py`)
Monitors retrigger patterns and generates alerts:
- Tracks retrigger behavior across tickets
- Identifies tickets hitting retrigger limits
- Detects high-frequency retrigger patterns
- Finds common failure reasons
- Identifies systemic issues affecting multiple tickets
- Generates comprehensive reports and dashboards

#### Usage

```python
from agents.monitoring import RetriggerMonitor, create_dashboard_data

# Initialize monitor
monitor = RetriggerMonitor(alert_threshold=2)

# Analyze retrigger states
all_states = cap_manager.get_all_retrigger_states()
report = monitor.analyze_all_states(all_states)

print(f"Total tickets: {report['total_tickets']}")
print(f"Tickets at limit: {report['tickets_at_limit']}")
print(f"Alerts: {len(report['alerts'])}")

# Generate human-readable report
print(monitor.generate_report())

# Create dashboard data
dashboard = create_dashboard_data(monitor)
```

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
   └─> Cap Manager checks retrigger eligibility
   └─> Executes ticket
   └─> Cap Manager records retrigger if needed
   └─> Checkpoints state
   └─> Handles failures
   └─> Monitoring alerts on issues
   
4. If interrupted:
   └─> State persisted in database
   └─> Can resume from last checkpoint
   └─> Skips completed tickets
   
5. Completion:
   └─> Marks state as COMPLETED
   └─> Reports summary
   └─> Resets Cap Manager state for completed tickets
```

## Dependencies

- `crewai` - AI agent framework
- `sqlalchemy` - Database ORM
- `psycopg2-binary` - PostgreSQL driver
- `pydantic` - Data validation

## Configuration

Environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `ANTHROPIC_API_KEY` - Claude API key for PM Agent
- `JIRA_*` - Jira API credentials (configured in tools/jira_client.py)
- `MAX_RETRIGGER_ATTEMPTS` - Max retrigger attempts (default: 3)
- `RETRIGGER_WINDOW_MINUTES` - Retrigger time window (default: 60)

## Testing

Run tests:
```bash
cd uat/backend
pytest tests/test_orchestrator.py -v
pytest tests/test_orchestrator_state.py -v

# Test Cap Manager Agent
pytest agents/tests/test_cap_manager_agent.py -v

# Test monitoring
pytest agents/tests/test_monitoring.py -v
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
- Dev Agent - Implements stories
- QA Agent - Tests implementations
- DevOps Agent - Handles deployments
- Security Agent - Performs security reviews
- Code Review Agent - Reviews pull requests
