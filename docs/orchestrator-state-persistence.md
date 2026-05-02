# Orchestrator State Persistence - Resume After Crash

**Ticket:** [SDT1-66]  
**Feature:** Orchestrator state persistence with crash recovery and resume capability

## Overview

The Orchestrator now persists its execution state to the database, enabling it to resume sprint execution after interruptions, crashes, or manual pauses. This ensures that sprint execution is resilient and can recover from failures without losing progress.

## Key Features

### 1. State Persistence
- **Database Storage**: All execution state is stored in the `orchestrator_states` table
- **Checkpoint System**: State is saved after each ticket completion/failure
- **Full State Tracking**: Tracks ticket queue, completed tickets, failed tickets, and current ticket

### 2. Resume Capability
- **Resume from Pause**: Continue execution after manual pause
- **Resume from Failure**: Retry after system crashes or errors
- **Preserved History**: Maintains completed and failed ticket lists across resume operations

### 3. Execution Control
- **Start**: Begin new sprint execution
- **Resume**: Continue from saved checkpoint
- **Pause**: Gracefully pause execution
- **Cancel**: Permanently cancel execution

## Architecture

### Database Model

The `OrchestratorState` model stores:

```python
class OrchestratorState(Base):
    id: UUID                          # Unique state identifier
    sprint_id: int                    # Jira sprint ID
    sprint_name: str                  # Sprint name
    jira_project_key: str            # Project key (e.g., 'SDT1')
    status: OrchestratorStatus       # Current status
    ticket_queue: List[str]          # Remaining tickets to execute
    completed_tickets: List[str]     # Successfully completed tickets
    failed_tickets: List[Dict]       # Failed tickets with error info
    current_ticket: str              # Currently executing ticket
    total_tickets: int               # Total ticket count
    started_at: datetime             # Execution start time
    completed_at: datetime           # Execution completion time
    last_checkpoint_at: datetime     # Last checkpoint time
    error_message: str               # Error message if failed
```

### Status Flow

```
PENDING → RUNNING → COMPLETED
                 → FAILED
                 → PAUSED → RUNNING (resume)
                 → CANCELLED
```

Only `PAUSED` and `FAILED` states can be resumed.

### Components

1. **StateManager** (`agents/orchestrator_state.py`)
   - Handles all database operations for state persistence
   - Provides methods for state transitions and checkpointing
   - Manages ticket tracking (completed, failed, remaining)

2. **Orchestrator** (`agents/orchestrator.py`)
   - Main execution engine
   - Integrates with StateManager for persistence
   - Handles ticket execution and error recovery

3. **API Router** (`uat/backend/orchestrator_router.py`)
   - REST API endpoints for orchestrator operations
   - Authenticated endpoints requiring user login
   - Provides progress monitoring and control

4. **CLI Tool** (`agents/orchestrator_cli.py`)
   - Command-line interface for orchestrator management
   - Useful for testing and manual operation

## Usage

### REST API

#### Start Sprint Execution

```http
POST /api/orchestrator/start
Authorization: Bearer <token>
Content-Type: application/json

{
  "sprint_id": 42,
  "sprint_name": "Sprint 10",
  "jira_project_key": "SDT1"
}
```

Response:
```json
{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "sprint_id": 42,
  "sprint_name": "Sprint 10",
  "status": "pending",
  "message": "Sprint execution initiated. State ID: ..."
}
```

#### Resume Execution

```http
POST /api/orchestrator/resume
Authorization: Bearer <token>
Content-Type: application/json

{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "jira_project_key": "SDT1"
}
```

#### Check Progress

```http
GET /api/orchestrator/progress/{state_id}
Authorization: Bearer <token>
```

Response:
```json
{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "sprint_id": 42,
  "sprint_name": "Sprint 10",
  "status": "running",
  "total_tickets": 10,
  "completed_tickets": 7,
  "failed_tickets": 1,
  "remaining_tickets": 2,
  "current_ticket": "SDT1-8",
  "progress_percentage": 70.0,
  "started_at": "2024-01-15T10:30:00Z",
  "last_checkpoint": "2024-01-15T11:45:00Z"
}
```

#### List Resumable States

```http
GET /api/orchestrator/resumable
Authorization: Bearer <token>
```

Response:
```json
{
  "states": [
    {
      "state_id": "550e8400-e29b-41d4-a716-446655440000",
      "sprint_id": 42,
      "sprint_name": "Sprint 10",
      "status": "paused",
      "total_tickets": 10,
      "completed": 5,
      "failed": 1,
      "remaining": 4,
      "last_updated": "2024-01-15T11:45:00Z"
    }
  ],
  "count": 1
}
```

#### Pause Execution

```http
POST /api/orchestrator/pause
Authorization: Bearer <token>
Content-Type: application/json

{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "reason": "Manual pause for maintenance"
}
```

#### Cancel Execution

```http
POST /api/orchestrator/cancel
Authorization: Bearer <token>
Content-Type: application/json

{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "reason": "Sprint cancelled"
}
```

### CLI Tool

#### Start Sprint

```bash
python agents/orchestrator_cli.py start \
  --sprint-id 42 \
  --sprint-name "Sprint 10" \
  --project SDT1
```

#### Resume Sprint

```bash
python agents/orchestrator_cli.py resume \
  --state-id 550e8400-e29b-41d4-a716-446655440000 \
  --project SDT1
```

#### List Resumable States

```bash
python agents/orchestrator_cli.py list-resumable
```

#### Check Progress

```bash
python agents/orchestrator_cli.py progress \
  --state-id 550e8400-e29b-41d4-a716-446655440000
```

#### Pause Execution

```bash
python agents/orchestrator_cli.py pause \
  --state-id 550e8400-e29b-41d4-a716-446655440000 \
  --reason "Manual pause"
```

#### Cancel Execution

```bash
python agents/orchestrator_cli.py cancel \
  --state-id 550e8400-e29b-41d4-a716-446655440000 \
  --reason "Sprint cancelled" \
  --yes
```

### Python API

#### Start Execution

```python
from agents.orchestrator import start_sprint_execution

state_id = start_sprint_execution(
    sprint_id=42,
    sprint_name="Sprint 10",
    jira_project_key="SDT1",
    verbose=True,
)
```

#### Resume Execution

```python
from agents.orchestrator import resume_sprint_execution

resume_sprint_execution(
    state_id=state_id,
    jira_project_key="SDT1",
    verbose=True,
)
```

#### Direct Orchestrator Usage

```python
from agents.orchestrator import Orchestrator
from database import SessionLocal

with SessionLocal() as db:
    orchestrator = Orchestrator(
        jira_project_key="SDT1",
        db=db,
        verbose=True,
    )
    
    # Start new sprint
    state_id = orchestrator.start_sprint(42, "Sprint 10")
    
    # Check progress
    progress = orchestrator.get_progress(state_id)
    
    # Resume later
    orchestrator.resume_sprint(state_id)
```

## Recovery Scenarios

### Scenario 1: System Crash During Execution

1. **Before Crash**: Orchestrator is executing tickets in sprint 42
   - State: RUNNING
   - Completed: SDT1-1, SDT1-2, SDT1-3
   - Current: SDT1-4
   - Queue: SDT1-5, SDT1-6, SDT1-7

2. **After Crash**: System restarts
   - State is preserved in database with last checkpoint
   - Current ticket may be incomplete

3. **Resume**:
   ```bash
   python agents/orchestrator_cli.py list-resumable
   python agents/orchestrator_cli.py resume --state-id <uuid> --project SDT1
   ```

4. **Behavior**:
   - Execution resumes from remaining queue
   - Completed tickets are not re-executed
   - Failed tickets are recorded with error details

### Scenario 2: Manual Pause for Maintenance

1. **Pause During Execution**:
   ```bash
   python agents/orchestrator_cli.py pause \
     --state-id <uuid> \
     --reason "Scheduled maintenance"
   ```

2. **Perform Maintenance**: System can be safely shut down

3. **Resume After Maintenance**:
   ```bash
   python agents/orchestrator_cli.py resume \
     --state-id <uuid> \
     --project SDT1
   ```

### Scenario 3: Ticket Failure Handling

1. **Ticket Fails**: SDT1-5 fails with error
   - Error is recorded in `failed_tickets` array
   - Ticket is removed from queue
   - Execution continues with remaining tickets

2. **View Failures**:
   ```bash
   python agents/orchestrator_cli.py progress --state-id <uuid>
   ```

3. **Review and Resume**:
   - Fix issues in failed tickets
   - Resume to process remaining tickets
   - Failed tickets remain in history for audit

## Testing

### Run Unit Tests

```bash
cd uat/backend
pytest test_orchestrator_state.py -v
```

Test coverage includes:
- State creation and retrieval
- State transitions
- Checkpoint saving
- Ticket completion/failure tracking
- Resume capability
- Progress tracking
- Error handling

### Example Test Output

```
test_orchestrator_state.py::test_create_state PASSED
test_orchestrator_state.py::test_get_state PASSED
test_orchestrator_state.py::test_start_execution PASSED
test_orchestrator_state.py::test_mark_ticket_completed PASSED
test_orchestrator_state.py::test_resume_from_paused_state PASSED
test_orchestrator_state.py::test_get_progress PASSED
... (42 tests total)
```

## Database Schema

The `orchestrator_states` table is created automatically by the ORM:

```sql
CREATE TABLE orchestrator_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sprint_id INTEGER NOT NULL,
    sprint_name VARCHAR(255) NOT NULL,
    jira_project_key VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    ticket_queue JSON NOT NULL DEFAULT '[]',
    completed_tickets JSON NOT NULL DEFAULT '[]',
    failed_tickets JSON NOT NULL DEFAULT '[]',
    current_ticket VARCHAR(50),
    total_tickets INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    last_checkpoint_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_orchestrator_states_sprint_id ON orchestrator_states(sprint_id);
```

## Monitoring and Observability

### Progress Tracking

Monitor execution progress in real-time:

```python
from agents.orchestrator_state import StateManager

with StateManager() as state_manager:
    progress = state_manager.get_progress(state_id)
    print(f"Progress: {progress['progress_percentage']}%")
    print(f"Completed: {progress['completed_tickets']}")
    print(f"Failed: {progress['failed_tickets']}")
    print(f"Remaining: {progress['remaining_tickets']}")
```

### Checkpoint History

Each checkpoint updates `last_checkpoint_at`:
- After each ticket completion
- After each ticket failure
- On pause/resume operations
- On status changes

### Error Tracking

Failed tickets include:
- Ticket key
- Error message
- Timestamp of failure

```json
{
  "ticket_key": "SDT1-5",
  "error_message": "Test execution failed: Connection timeout",
  "timestamp": "2024-01-15T11:30:00Z"
}
```

## Best Practices

1. **Regular Checkpoints**: StateManager automatically checkpoints after each ticket
2. **Error Handling**: All ticket failures are recorded for audit trail
3. **Graceful Shutdown**: Use pause before system shutdown
4. **Monitor Progress**: Check progress regularly during long-running executions
5. **Review Failures**: Analyze failed tickets before resuming
6. **Clean Up**: Archive or delete old completed states periodically

## Future Enhancements

- **Automatic Retry**: Configurable retry logic for failed tickets
- **Parallel Execution**: Execute independent tickets in parallel
- **Dependency Management**: Handle ticket dependencies explicitly
- **Progress Webhooks**: Notify external systems of progress
- **State Archival**: Automatic archival of completed states
- **Performance Metrics**: Track execution times per ticket

## Troubleshooting

### State Not Found

**Error**: `State {uuid} not found`

**Solution**: Verify the state ID is correct using `list-resumable`

### Cannot Resume

**Error**: `Cannot resume state with status running`

**Solution**: Only PAUSED or FAILED states can be resumed. Cancel or wait for completion.

### Database Connection Issues

**Error**: `DATABASE_URL environment variable is not set`

**Solution**: Set DATABASE_URL environment variable:
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
```

### Stale Checkpoints

If a state remains RUNNING after a crash, it won't appear in resumable list.

**Solution**: Manually update the state status:
```python
from agents.orchestrator_state import StateManager

with StateManager() as state_manager:
    state_manager.fail_execution(state_id, "System crash - marking for resume")
```

## References

- **Ticket**: [SDT1-66] Orchestrator state persistence - resume after crash
- **Related Files**:
  - `agents/orchestrator.py` - Main orchestrator implementation
  - `agents/orchestrator_state.py` - State management
  - `uat/backend/orchestrator_router.py` - REST API
  - `agents/orchestrator_cli.py` - CLI tool
  - `uat/backend/models.py` - Database models
  - `uat/backend/test_orchestrator_state.py` - Unit tests
