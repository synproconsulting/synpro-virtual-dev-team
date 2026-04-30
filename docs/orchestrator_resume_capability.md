# Orchestrator Resume Capability

## Overview

The Orchestrator is responsible for sequencing and executing stories from a sprint in dependency order. This implementation adds state persistence and resume capability, allowing the orchestrator to recover from failures, interruptions, or manual pauses.

## Key Features

### 1. State Persistence
- All execution state is persisted to PostgreSQL database
- State includes: ticket queue, completed tickets, failed tickets, current ticket
- Automatic checkpointing after each ticket completion
- Metadata tracked: start time, completion time, last checkpoint, error messages

### 2. Resume Capability
- Resume execution from any paused or failed state
- Continues from last checkpoint without re-executing completed tickets
- Preserves execution order and dependencies
- Handles partial completions gracefully

### 3. Progress Tracking
- Real-time progress monitoring
- Detailed statistics: total, completed, failed, remaining tickets
- Progress percentage calculation
- Timestamp tracking for all state changes

### 4. Error Handling
- Graceful handling of ticket execution failures
- Detailed error logging per failed ticket
- Continues execution with remaining tickets after failures
- Option to pause on critical errors

## Architecture

### Database Schema

```sql
CREATE TABLE orchestrator_states (
    id UUID PRIMARY KEY,
    sprint_id INTEGER NOT NULL,
    sprint_name VARCHAR(255) NOT NULL,
    jira_project_key VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- PENDING, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED
    ticket_queue JSON NOT NULL,
    completed_tickets JSON NOT NULL,
    failed_tickets JSON NOT NULL,
    current_ticket VARCHAR(50),
    total_tickets INTEGER NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    last_checkpoint_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### Core Components

#### 1. OrchestratorState Model (`uat/backend/models.py`)
- SQLAlchemy model for state persistence
- Enum for status values
- JSON fields for flexible ticket tracking

#### 2. StateManager (`agents/orchestrator_state.py`)
- Manages state CRUD operations
- Checkpoint management
- Progress tracking
- State transitions (pending → running → completed/failed/paused)

#### 3. Orchestrator (`agents/orchestrator.py`)
- Main orchestrator logic
- Sprint execution
- Ticket execution loop
- Resume capability
- Error handling

#### 4. CLI Tool (`agents/orchestrator_cli.py`)
- Command-line interface for orchestrator management
- Start, resume, pause, cancel operations
- Progress monitoring
- List resumable executions

## Usage

### Starting a Sprint

```python
from agents.orchestrator import Orchestrator

with Orchestrator(jira_project_key="SDT1", verbose=True) as orch:
    state_id = orch.start_sprint(
        sprint_id=123,
        sprint_name="Sprint 1",
    )
    print(f"State ID: {state_id}")
```

### Resuming a Sprint

```python
from uuid import UUID
from agents.orchestrator import Orchestrator

state_id = UUID("...")  # From previous execution

with Orchestrator(jira_project_key="SDT1", verbose=True) as orch:
    orch.resume_sprint(state_id)
```

### Checking Progress

```python
from agents.orchestrator import Orchestrator

with Orchestrator(jira_project_key="SDT1") as orch:
    progress = orch.get_progress(state_id)
    print(f"Progress: {progress['progress_percentage']}%")
    print(f"Completed: {progress['completed_tickets']}/{progress['total_tickets']}")
```

### Listing Resumable Sprints

```python
from agents.orchestrator import Orchestrator

with Orchestrator(jira_project_key="SDT1") as orch:
    resumable = orch.list_resumable()
    for sprint in resumable:
        print(f"{sprint['sprint_name']}: {sprint['status']}")
```

### Pausing Execution

```python
from agents.orchestrator import Orchestrator

with Orchestrator(jira_project_key="SDT1") as orch:
    orch.pause(state_id, reason="Manual intervention required")
```

### Cancelling Execution

```python
from agents.orchestrator import Orchestrator

with Orchestrator(jira_project_key="SDT1") as orch:
    orch.cancel(state_id, reason="Sprint cancelled by PM")
```

## CLI Usage

### Start a Sprint
```bash
python agents/orchestrator_cli.py start \
    --sprint-id 123 \
    --sprint-name "Sprint 1" \
    --project SDT1
```

### Resume a Sprint
```bash
python agents/orchestrator_cli.py resume \
    --state-id <uuid> \
    --project SDT1
```

### List Resumable Sprints
```bash
python agents/orchestrator_cli.py list --project SDT1
```

### Check Progress
```bash
python agents/orchestrator_cli.py progress \
    --state-id <uuid> \
    --project SDT1
```

### Pause Execution
```bash
python agents/orchestrator_cli.py pause \
    --state-id <uuid> \
    --project SDT1 \
    --reason "Waiting for deployment"
```

### Cancel Execution
```bash
python agents/orchestrator_cli.py cancel \
    --state-id <uuid> \
    --project SDT1 \
    --reason "Sprint cancelled"
```

## State Transitions

```
PENDING ──[start_execution]──> RUNNING
                                   │
                                   ├──[pause]──> PAUSED ──[resume]──┐
                                   │                                  │
                                   ├──[error]──> FAILED ──[resume]───┤
                                   │                                  │
                                   ├──[cancel]──> CANCELLED          │
                                   │                                  │
                                   └──[complete]──> COMPLETED    <────┘
```

## Error Handling Strategy

### Ticket-Level Failures
- Individual ticket failures are logged but don't stop execution
- Failed tickets are recorded with error messages
- Orchestrator continues with remaining tickets
- Sprint can complete successfully even with some failed tickets

### Critical Failures
- System-level errors (database, network) fail the entire execution
- State is marked as FAILED with error message
- Can be resumed once the issue is resolved

### Resume After Failure
- Resume from FAILED status picks up from last checkpoint
- Does not re-execute completed tickets
- Can retry failed tickets if desired (future enhancement)

## Integration with PM Agent

The Orchestrator reads `execution_order` (customfield_10071) from Jira tickets:

1. PM Agent sets `execution_order` on every story during sprint planning
2. Orchestrator fetches all tickets in sprint
3. Sorts tickets by `execution_order` ascending
4. Executes tickets sequentially in order
5. Dependencies are satisfied by execution order

## Database Migration

Run the migration to create the `orchestrator_states` table:

```bash
cd uat/backend
python -m migrations.add_orchestrator_state
```

To rollback:
```bash
python -m migrations.add_orchestrator_state --downgrade
```

## Testing

### Run Tests
```bash
cd uat/backend
pytest tests/test_orchestrator_state.py -v
pytest tests/test_orchestrator.py -v
```

### Test Coverage
- State management CRUD operations
- State transitions
- Checkpoint functionality
- Resume capability
- Error handling
- Progress tracking

## Future Enhancements

1. **Retry Logic**: Automatic retry of failed tickets with backoff
2. **Parallel Execution**: Execute independent tickets in parallel
3. **Priority Override**: Manual priority adjustments during execution
4. **Webhooks**: Notify external systems of state changes
5. **UI Dashboard**: Real-time visualization of execution progress
6. **Execution History**: Archive completed states for analytics
7. **Smart Resume**: Analyze failures and suggest resolution before resume
8. **Dependency Graph**: Visualize ticket dependencies and execution flow

## Troubleshooting

### State Not Found
- Verify the state ID is correct
- Check database connection
- Ensure state wasn't deleted

### Cannot Resume
- Only PAUSED or FAILED states can be resumed
- Check current state status
- COMPLETED or CANCELLED states cannot be resumed

### Tickets Not Executing
- Verify execution_order is set on all tickets
- Check Jira API connectivity
- Review orchestrator logs
- Ensure tickets are in the correct sprint

### Database Connection Issues
- Verify DATABASE_URL environment variable
- Check PostgreSQL service is running
- Verify database credentials
- Check network connectivity

## Best Practices

1. **Always Set execution_order**: PM Agent must set execution_order on every story
2. **Monitor Progress**: Check progress regularly during long executions
3. **Handle Failures Promptly**: Review failed tickets and resolve issues quickly
4. **Use Meaningful State IDs**: Track state IDs for important sprints
5. **Clean Up Old States**: Archive or delete old completed states periodically
6. **Test in Staging**: Test resume capability in staging before production use
7. **Document Dependencies**: Clear dependency documentation helps with troubleshooting
8. **Set Reasonable Checkpoints**: Current implementation checkpoints after each ticket

## Security Considerations

1. **Database Access**: Orchestrator requires read/write access to database
2. **Jira Credentials**: Store Jira API credentials securely in environment variables
3. **State Access Control**: Consider adding user-level access control to states
4. **Audit Logging**: Log all state changes for compliance and troubleshooting
5. **Error Messages**: Be careful not to leak sensitive information in error messages

## Performance Considerations

1. **Checkpoint Frequency**: Current implementation checkpoints after each ticket (good for resume, slight overhead)
2. **Database Load**: Each checkpoint writes to database
3. **JSON Fields**: Ticket queues stored as JSON; consider limits for very large sprints
4. **Concurrent Executions**: Multiple sprints can run concurrently (different state IDs)
5. **Query Optimization**: Index on sprint_id and status for fast lookups

## Support

For questions or issues:
1. Check this documentation
2. Review test cases for examples
3. Check orchestrator logs
4. Examine database state
5. Contact development team
