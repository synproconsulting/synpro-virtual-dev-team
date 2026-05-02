# Orchestrator State Persistence - Resume After Crash

## Overview

The Orchestrator State Persistence feature enables the Sprint Orchestrator to save its execution state to the database after each ticket completion. This allows the orchestrator to resume sprint execution from the last checkpoint after crashes, failures, or manual interruptions.

## Key Features

- **Automatic Checkpointing**: State is saved after each ticket completion
- **Resume Capability**: Continue execution from where it left off after any interruption
- **Progress Tracking**: Monitor execution progress in real-time
- **Failure Recording**: Detailed error information for failed tickets
- **Pause/Resume**: Manually pause and resume executions
- **Multiple Sprint Support**: Track and resume multiple sprint executions concurrently

## Architecture

### Components

1. **OrchestratorState Model** (`models.py`)
   - Database model for persisting execution state
   - Stores sprint information, ticket queues, and execution metadata
   - Uses PostgreSQL JSON fields for flexible state storage

2. **StateManager** (`agents/orchestrator_state.py`)
   - Manages state persistence and recovery operations
   - Provides checkpoint, resume, pause, and cancel operations
   - Tracks progress and execution statistics

3. **Orchestrator** (`agents/orchestrator.py`)
   - Main orchestrator class with resume capability
   - Executes tickets in sequence based on execution_order
   - Integrates with StateManager for automatic checkpointing

4. **API Router** (`uat/backend/orchestrator_router.py`)
   - REST API endpoints for orchestrator operations
   - Enables remote control and monitoring of executions

5. **CLI Tool** (`tools/orchestrator_cli.py`)
   - Command-line interface for managing executions
   - Provides human-friendly output and error messages

## Database Schema

### orchestrator_states Table

```sql
CREATE TABLE orchestrator_states (
    id UUID PRIMARY KEY,
    sprint_id INTEGER NOT NULL,
    sprint_name VARCHAR(255) NOT NULL,
    jira_project_key VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- pending, running, paused, completed, failed, cancelled
    
    -- State tracking
    ticket_queue JSON NOT NULL,        -- List of ticket keys remaining
    completed_tickets JSON NOT NULL,   -- List of completed ticket keys
    failed_tickets JSON NOT NULL,      -- List of failed tickets with errors
    current_ticket VARCHAR(50),        -- Currently executing ticket
    
    -- Metadata
    total_tickets INTEGER NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    last_checkpoint_at TIMESTAMP,
    error_message TEXT,
    
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_orchestrator_states_sprint_id ON orchestrator_states(sprint_id);
CREATE INDEX idx_orchestrator_states_status ON orchestrator_states(status);
```

## Usage

### Python API

#### Starting a Sprint Execution

```python
from agents.orchestrator import Orchestrator

with Orchestrator(jira_project_key="SDT1", verbose=True) as orchestrator:
    state_id = orchestrator.start_sprint(
        sprint_id=123,
        sprint_name="Sprint 10",
    )
    print(f"Started execution with state ID: {state_id}")
```

#### Resuming After a Crash

```python
from agents.orchestrator import Orchestrator
from uuid import UUID

state_id = UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

with Orchestrator(jira_project_key="SDT1", verbose=True) as orchestrator:
    orchestrator.resume_sprint(state_id)
```

#### Checking Progress

```python
from agents.orchestrator_state import StateManager
from uuid import UUID

state_id = UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

with StateManager() as state_manager:
    progress = state_manager.get_progress(state_id)
    print(f"Progress: {progress['progress_percentage']:.1f}%")
    print(f"Completed: {progress['completed_tickets']}/{progress['total_tickets']}")
    print(f"Failed: {progress['failed_tickets']}")
```

#### Listing Resumable States

```python
from agents.orchestrator import Orchestrator

with Orchestrator(jira_project_key="SDT1", verbose=False) as orchestrator:
    resumable = orchestrator.list_resumable()
    for state in resumable:
        print(f"{state['sprint_name']}: {state['status']} ({state['remaining']} tickets remaining)")
```

### REST API

#### Start a Sprint

```bash
curl -X POST http://localhost:8000/api/orchestrator/start \
  -H "Content-Type: application/json" \
  -d '{
    "sprint_id": 123,
    "sprint_name": "Sprint 10",
    "jira_project_key": "SDT1"
  }'
```

Response:
```json
{
  "success": true,
  "state_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "sprint_id": 123,
  "sprint_name": "Sprint 10",
  "message": "Sprint execution started. State ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

#### Resume a Sprint

```bash
curl -X POST http://localhost:8000/api/orchestrator/resume \
  -H "Content-Type: application/json" \
  -d '{
    "state_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "jira_project_key": "SDT1"
  }'
```

#### Check Progress

```bash
curl http://localhost:8000/api/orchestrator/progress/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

Response:
```json
{
  "state_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "sprint_id": 123,
  "sprint_name": "Sprint 10",
  "status": "running",
  "total_tickets": 10,
  "completed_tickets": 7,
  "failed_tickets": 1,
  "remaining_tickets": 2,
  "current_ticket": "SDT1-45",
  "progress_percentage": 80.0,
  "started_at": "2024-01-15T10:30:00Z",
  "last_checkpoint": "2024-01-15T11:45:30Z"
}
```

#### List Resumable States

```bash
curl http://localhost:8000/api/orchestrator/resumable
```

#### Pause Execution

```bash
curl -X POST http://localhost:8000/api/orchestrator/pause \
  -H "Content-Type: application/json" \
  -d '{
    "state_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "reason": "Manual pause for debugging"
  }'
```

#### Cancel Execution

```bash
curl -X POST http://localhost:8000/api/orchestrator/cancel \
  -H "Content-Type: application/json" \
  -d '{
    "state_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "reason": "Sprint cancelled"
  }'
```

### CLI Tool

#### Start a Sprint

```bash
python tools/orchestrator_cli.py start 123 "Sprint 10" --project SDT1
```

#### Resume After Crash

```bash
python tools/orchestrator_cli.py resume a1b2c3d4-e5f6-7890-abcd-ef1234567890 --project SDT1
```

#### Check Status

```bash
python tools/orchestrator_cli.py status a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

Output:
```
Execution Status
State ID:           a1b2c3d4-e5f6-7890-abcd-ef1234567890
Sprint:             Sprint 10 (ID: 123)
Status:             running
Progress:           80.0%
Total Tickets:      10
Completed:          7
Failed:             1
Remaining:          2
Current Ticket:     SDT1-45
Started:            2024-01-15T10:30:00Z
Last Checkpoint:    2024-01-15T11:45:30Z
```

#### List Resumable States

```bash
python tools/orchestrator_cli.py list-resumable
```

Output:
```
Resumable States (2 found)

State ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
  Sprint:      Sprint 10 (ID: 123)
  Status:      paused
  Progress:    7/10 completed
  Failed:      1
  Remaining:   2
  Last Update: 2024-01-15T11:45:30
  ℹ Use 'resume a1b2c3d4-e5f6-7890-abcd-ef1234567890' to continue

State ID: b2c3d4e5-f6a7-8901-bcde-f12345678901
  Sprint:      Sprint 9 (ID: 122)
  Status:      failed
  Progress:    5/8 completed
  Failed:      1
  Remaining:   2
  Last Update: 2024-01-14T16:20:15
  ⚠ Use 'resume b2c3d4e5-f6a7-8901-bcde-f12345678901' to retry
```

#### Pause Execution

```bash
python tools/orchestrator_cli.py pause a1b2c3d4-e5f6-7890-abcd-ef1234567890 --reason "Manual pause"
```

#### Cancel Execution

```bash
python tools/orchestrator_cli.py cancel a1b2c3d4-e5f6-7890-abcd-ef1234567890 --reason "Sprint cancelled"
```

## State Transitions

```
PENDING → RUNNING → COMPLETED
            ↓
            PAUSED → RUNNING
            ↓
            FAILED → RUNNING (via resume)
            ↓
            CANCELLED (terminal)
```

### State Descriptions

- **PENDING**: State created, execution not yet started
- **RUNNING**: Actively executing tickets
- **PAUSED**: Manually paused, can be resumed
- **COMPLETED**: All tickets processed successfully
- **FAILED**: Execution encountered an error, can be resumed
- **CANCELLED**: Execution cancelled, cannot be resumed

## Error Handling

### Ticket Execution Failures

When a ticket fails:
1. Error is logged with full stack trace
2. Ticket is removed from queue
3. Ticket is added to `failed_tickets` with error details
4. Execution continues with next ticket (fail-fast disabled by default)
5. State is checkpointed after failure

### Orchestrator Crashes

When the orchestrator crashes:
1. Last checkpoint remains in database
2. Execution can be resumed from last checkpoint
3. Current ticket (if any) will be retried
4. Completed tickets will not be re-executed

### Database Connection Failures

If database connection fails during execution:
1. State may not be saved to last checkpoint
2. Resume from previous successful checkpoint
3. Some tickets may need to be re-executed

## Configuration

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:port/dbname
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token

# Optional
JIRA_PROJECT_KEY=SDT1  # Default project key for CLI
LOG_LEVEL=INFO         # Logging level
```

### Orchestrator Options

```python
Orchestrator(
    jira_project_key: str,  # Jira project key (e.g., 'SDT1')
    db: Optional[Session] = None,  # Database session (creates new if None)
    verbose: bool = True,  # Enable detailed logging
)
```

## Testing

### Run Unit Tests

```bash
# Test state manager
pytest uat/backend/tests/test_orchestrator_state.py -v

# Test orchestrator
pytest uat/backend/tests/test_orchestrator.py -v

# Test with coverage
pytest uat/backend/tests/test_orchestrator*.py --cov=agents --cov-report=term-missing
```

### Manual Testing

1. Start a sprint execution
2. Kill the process mid-execution (Ctrl+C)
3. Resume using the state ID
4. Verify execution continues from last checkpoint

```bash
# Terminal 1: Start execution
python tools/orchestrator_cli.py start 123 "Test Sprint" --project SDT1

# Note the state ID from output
# Kill with Ctrl+C after a few tickets

# Terminal 2: Resume execution
python tools/orchestrator_cli.py resume <state-id> --project SDT1
```

## Performance Considerations

### Checkpoint Frequency

- Checkpoint after every ticket completion
- Trade-off: More frequent = slower but safer
- Current implementation: Optimal for most use cases

### Database Load

- Each checkpoint is a single UPDATE query
- Minimal impact on database performance
- JSON fields indexed for fast queries

### Memory Usage

- State kept in memory during execution
- Periodic sync to database
- Scales to hundreds of tickets per sprint

## Best Practices

1. **Always capture state ID**: Save the state ID returned by `start_sprint()` for resume capability

2. **Monitor progress**: Use progress endpoints to track execution

3. **Handle failures gracefully**: Use try/catch blocks when starting/resuming

4. **Clean up old states**: Periodically archive or delete completed states

5. **Test resume capability**: Regularly test crash recovery in development

6. **Use meaningful sprint names**: Makes it easier to identify states

7. **Log failures**: Review failed tickets and fix issues before resuming

## Troubleshooting

### "State not found" Error

- Verify state ID is correct (UUID format)
- Check database connectivity
- Ensure state hasn't been deleted

### "Cannot resume" Error

- Check state status (must be PAUSED or FAILED)
- Completed and cancelled states cannot be resumed
- Create new execution if needed

### Tickets Re-executing

- May occur if checkpoint failed
- Safe: Ticket execution is idempotent
- Review logs to identify checkpoint failures

### Database Connection Issues

```python
# Test database connection
from database import SessionLocal
db = SessionLocal()
try:
    db.execute("SELECT 1")
    print("✓ Database connected")
except Exception as e:
    print(f"✗ Database error: {e}")
finally:
    db.close()
```

## Future Enhancements

- [ ] Parallel ticket execution with state locking
- [ ] Automated retry with exponential backoff
- [ ] State archival and cleanup jobs
- [ ] Real-time WebSocket progress updates
- [ ] Execution analytics and reporting
- [ ] Rollback capability for failed tickets
- [ ] Multi-sprint orchestration
- [ ] Cloud state backup and recovery

## Related Documentation

- [Orchestrator Architecture](./orchestrator-architecture.md)
- [Jira Integration](./jira-integration.md)
- [Database Schema](./database-schema.md)
- [API Reference](./api-reference.md)

## Support

For issues or questions:
- Check logs: `tail -f logs/orchestrator.log`
- Review failed tickets: `python tools/orchestrator_cli.py status <state-id>`
- Contact: dev-team@synpro.ai
