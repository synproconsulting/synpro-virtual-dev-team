# Orchestrator State Persistence & Resume

This document describes the orchestrator state persistence and resume functionality implemented in [SDT1-66].

## Overview

The Orchestrator now persists its execution state to the database, enabling it to resume sprint execution after crashes, interruptions, or manual pauses. This ensures that work is never lost and sprints can continue from where they left off.

## Features

- **Automatic State Persistence**: All execution state is saved to the database after each ticket completion
- **Crash Recovery**: Resume execution after unexpected failures or crashes
- **Manual Pause/Resume**: Pause execution manually and resume later
- **Progress Tracking**: Monitor execution progress in real-time
- **Failed Ticket Tracking**: Keep detailed records of failed tickets with error messages
- **Multiple Interface Support**: Manage state via CLI or REST API

## Architecture

### Database Schema

The `orchestrator_states` table tracks execution state:

```sql
CREATE TABLE orchestrator_states (
    id                  UUID PRIMARY KEY,
    sprint_id           INTEGER NOT NULL,
    sprint_name         VARCHAR(255) NOT NULL,
    jira_project_key    VARCHAR(50) NOT NULL,
    status              VARCHAR(20) NOT NULL,  -- PENDING, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED
    ticket_queue        JSON NOT NULL,         -- Remaining tickets to execute
    completed_tickets   JSON NOT NULL,         -- Completed ticket keys
    failed_tickets      JSON NOT NULL,         -- Failed tickets with error info
    current_ticket      VARCHAR(50),           -- Currently executing ticket
    total_tickets       INTEGER NOT NULL,
    started_at          TIMESTAMP,
    completed_at        TIMESTAMP,
    last_checkpoint_at  TIMESTAMP,
    error_message       TEXT,
    created_at          TIMESTAMP NOT NULL,
    updated_at          TIMESTAMP NOT NULL
);
```

### Status Flow

```
PENDING → RUNNING → COMPLETED
    ↓         ↓
    ↓      PAUSED → RUNNING (resume)
    ↓         ↓
    ↓      FAILED → RUNNING (resume)
    ↓
  CANCELLED
```

### State Persistence

State is persisted at these checkpoints:

1. **Sprint Start**: Initial state created with ticket queue
2. **Before Each Ticket**: Current ticket updated
3. **After Each Ticket**: Completed/failed tickets updated, queue updated
4. **Manual Actions**: Pause, cancel, or resume operations

## Usage

### 1. Command-Line Interface (CLI)

The CLI tool provides a simple interface for managing orchestrator state.

#### Start a Sprint

```bash
python -m agents.cli start \
    --sprint-id 123 \
    --sprint-name "Sprint 42" \
    --project SDT1
```

Output:
```
Starting sprint 123: Sprint 42
Project: SDT1

[ORCHESTRATOR] Fetching tickets for sprint 123
[ORCHESTRATOR] Executing 5 tickets
[ORCHESTRATOR] Processing ticket: SDT1-101
...

✓ Sprint execution completed
State ID: 550e8400-e29b-41d4-a716-446655440000

To check progress or resume later, use:
  python -m agents.cli progress --state-id 550e8400-e29b-41d4-a716-446655440000
  python -m agents.cli resume --state-id 550e8400-e29b-41d4-a716-446655440000 --project SDT1
```

#### Resume a Sprint

```bash
python -m agents.cli resume \
    --state-id 550e8400-e29b-41d4-a716-446655440000 \
    --project SDT1
```

#### List Resumable Sprints

```bash
python -m agents.cli list-resumable
```

Output:
```
Found 2 resumable sprint(s):

State ID:     550e8400-e29b-41d4-a716-446655440000
Sprint:       #123 - Sprint 42
Status:       PAUSED
Progress:     3/5 completed, 0 failed, 2 remaining
Last updated: 2024-01-15T10:30:00

State ID:     660e8400-e29b-41d4-a716-446655440001
Sprint:       #124 - Sprint 43
Status:       FAILED
Progress:     2/8 completed, 1 failed, 5 remaining
Last updated: 2024-01-15T09:15:00
```

#### Check Progress

```bash
python -m agents.cli progress \
    --state-id 550e8400-e29b-41d4-a716-446655440000
```

Output:
```
Sprint Progress
============================================================
State ID:         550e8400-e29b-41d4-a716-446655440000
Sprint:           #123 - Sprint 42
Status:           RUNNING
Progress:         60.0%

Total tickets:    5
Completed:        3
Failed:           0
Remaining:        2

Current ticket:   SDT1-104
Started at:       2024-01-15T10:00:00
Last checkpoint:  2024-01-15T10:28:30
```

#### Pause Execution

```bash
python -m agents.cli pause \
    --state-id 550e8400-e29b-41d4-a716-446655440000 \
    --reason "Maintenance required"
```

#### Cancel Execution

```bash
python -m agents.cli cancel \
    --state-id 550e8400-e29b-41d4-a716-446655440000 \
    --reason "Sprint cancelled by PM"
```

### 2. REST API

The orchestrator provides REST API endpoints for integration with other systems.

#### Start Sprint Execution

```http
POST /api/orchestrator/start
Content-Type: application/json

{
  "sprint_id": 123,
  "sprint_name": "Sprint 42",
  "jira_project_key": "SDT1"
}
```

Response (201 Created):
```json
{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "sprint_id": 123,
  "sprint_name": "Sprint 42",
  "status": "running",
  "message": "Sprint execution started with state ID 550e8400-e29b-41d4-a716-446655440000"
}
```

#### Resume Sprint Execution

```http
POST /api/orchestrator/resume
Content-Type: application/json

{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "jira_project_key": "SDT1"
}
```

Response (200 OK):
```json
{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "sprint_id": 123,
  "sprint_name": "Sprint 42",
  "status": "completed",
  "message": "Sprint execution resumed and completed with status completed"
}
```

#### Get Progress

```http
GET /api/orchestrator/progress/550e8400-e29b-41d4-a716-446655440000
```

Response (200 OK):
```json
{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "sprint_id": 123,
  "sprint_name": "Sprint 42",
  "status": "running",
  "total_tickets": 5,
  "completed_tickets": 3,
  "failed_tickets": 0,
  "remaining_tickets": 2,
  "current_ticket": "SDT1-104",
  "progress_percentage": 60.0,
  "started_at": "2024-01-15T10:00:00",
  "last_checkpoint": "2024-01-15T10:28:30"
}
```

#### List Resumable Sprints

```http
GET /api/orchestrator/resumable
```

Response (200 OK):
```json
[
  {
    "state_id": "550e8400-e29b-41d4-a716-446655440000",
    "sprint_id": 123,
    "sprint_name": "Sprint 42",
    "status": "paused",
    "total_tickets": 5,
    "completed": 3,
    "failed": 0,
    "remaining": 2,
    "last_updated": "2024-01-15T10:30:00"
  }
]
```

#### Pause Execution

```http
POST /api/orchestrator/pause
Content-Type: application/json

{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "reason": "Maintenance required"
}
```

Response (200 OK):
```json
{
  "success": true,
  "message": "Sprint execution paused: Maintenance required",
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "paused"
}
```

#### Cancel Execution

```http
POST /api/orchestrator/cancel
Content-Type: application/json

{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "reason": "Sprint cancelled by PM"
}
```

Response (200 OK):
```json
{
  "success": true,
  "message": "Sprint execution cancelled: Sprint cancelled by PM",
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled"
}
```

### 3. Python API

Direct programmatic access is available via the Orchestrator class.

```python
from agents.orchestrator import Orchestrator, start_sprint_execution, resume_sprint_execution
from uuid import UUID

# Start a sprint
state_id = start_sprint_execution(
    sprint_id=123,
    sprint_name="Sprint 42",
    jira_project_key="SDT1",
    verbose=True,
)

# Check progress
with Orchestrator("SDT1") as orchestrator:
    progress = orchestrator.get_progress(state_id)
    print(f"Progress: {progress['progress_percentage']}%")
    
    # List resumable
    resumable = orchestrator.list_resumable()
    for sprint in resumable:
        print(f"{sprint['sprint_name']}: {sprint['status']}")
    
    # Pause
    orchestrator.pause(state_id, "Manual pause")
    
    # Resume later
    orchestrator.resume_sprint(state_id)
```

## Recovery Scenarios

### Scenario 1: Application Crash

**Situation**: The orchestrator crashes while executing ticket SDT1-103 (ticket 3 of 5).

**State Before Crash**:
- Completed: SDT1-101, SDT1-102
- Current: SDT1-103 (in progress)
- Remaining: SDT1-104, SDT1-105

**Recovery**:
1. List resumable sprints: `python -m agents.cli list-resumable`
2. Resume execution: `python -m agents.cli resume --state-id <uuid> --project SDT1`

**State After Resume**:
- Completed: SDT1-101, SDT1-102
- Failed: SDT1-103 (marked as failed with crash info)
- Remaining: SDT1-104, SDT1-105 (execution continues)

### Scenario 2: Manual Pause for Maintenance

**Situation**: Operations team needs to perform database maintenance.

**Actions**:
1. Pause execution: `python -m agents.cli pause --state-id <uuid> --reason "DB maintenance"`
2. Perform maintenance
3. Resume execution: `python -m agents.cli resume --state-id <uuid> --project SDT1`

### Scenario 3: Ticket Execution Failure

**Situation**: A ticket fails during execution (e.g., tests fail, deployment error).

**Behavior**:
- Failed ticket is recorded with error details
- Execution continues with remaining tickets
- Failed tickets can be retried manually or investigated

**View Failed Tickets**:
```python
from agents.orchestrator_state import StateManager

with StateManager() as state_manager:
    state = state_manager.get_state(state_id)
    for failure in state.failed_tickets:
        print(f"{failure['ticket_key']}: {failure['error_message']}")
```

## Best Practices

### 1. Monitor Progress Regularly

```bash
# Set up a monitoring script
while true; do
    python -m agents.cli progress --state-id $STATE_ID
    sleep 60
done
```

### 2. Handle Interrupts Gracefully

The orchestrator saves state after each ticket, so interrupting with Ctrl+C is safe:

```bash
python -m agents.cli start --sprint-id 123 --sprint-name "Sprint 42" --project SDT1
# Press Ctrl+C
# Resume later:
python -m agents.cli list-resumable
python -m agents.cli resume --state-id <uuid> --project SDT1
```

### 3. Review Failed Tickets

Before resuming a failed sprint, review the failed tickets:

```bash
python -m agents.cli progress --state-id <uuid>
```

Check the database for detailed error messages:

```sql
SELECT failed_tickets FROM orchestrator_states WHERE id = '<uuid>';
```

### 4. Clean Up Completed States

Periodically clean up old completed states:

```sql
DELETE FROM orchestrator_states 
WHERE status = 'completed' 
  AND completed_at < NOW() - INTERVAL '30 days';
```

## Troubleshooting

### State Not Found

**Error**: "State {uuid} not found"

**Solution**: Verify the state ID is correct:
```bash
python -m agents.cli list-resumable
```

### Cannot Resume State

**Error**: "Cannot resume state with status completed"

**Solution**: Only PAUSED or FAILED states can be resumed. Check status:
```bash
python -m agents.cli progress --state-id <uuid>
```

### Database Connection Error

**Error**: "Database initialization error: ..."

**Solution**: Ensure DATABASE_URL environment variable is set:
```bash
export DATABASE_URL="postgresql://user:password@host:5432/database"
```

## Performance Considerations

### State Persistence Overhead

- **Checkpoint Frequency**: State is saved after each ticket (~1-2 seconds overhead)
- **JSON Storage**: Ticket lists are stored as JSON (efficient for small-medium sprints)
- **Database I/O**: Uses database transactions for consistency

### Scaling Recommendations

- **Large Sprints** (>100 tickets): Consider batching checkpoints every N tickets
- **Concurrent Sprints**: Each sprint gets its own state; no contention
- **Long-Running Sprints**: State size remains constant (completed tickets move from queue)

## Future Enhancements

Potential improvements for future iterations:

1. **Checkpoint Batching**: Save state every N tickets instead of every ticket
2. **Distributed Execution**: Support parallel ticket execution with state sharding
3. **State Snapshots**: Create named snapshots for rollback
4. **Webhook Notifications**: Send notifications on pause, failure, or completion
5. **Retry Policies**: Automatic retry of failed tickets with exponential backoff
6. **State Compression**: Compress large ticket queues for storage efficiency

## Related Documentation

- [Orchestrator Architecture](orchestrator-architecture.md)
- [Database Schema](database-schema.md)
- [API Reference](api-reference.md)
- [Deployment Guide](deployment.md)
