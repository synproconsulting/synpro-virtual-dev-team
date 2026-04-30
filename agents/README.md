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
   └─> Executes ticket
   └─> Checkpoints state
   └─> Handles failures
   
4. If interrupted:
   └─> State persisted in database
   └─> Can resume from last checkpoint
   └─> Skips completed tickets
   
5. Completion:
   └─> Marks state as COMPLETED
   └─> Reports summary
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

## Testing

Run tests:
```bash
cd uat/backend
pytest tests/test_orchestrator.py -v
pytest tests/test_orchestrator_state.py -v
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
