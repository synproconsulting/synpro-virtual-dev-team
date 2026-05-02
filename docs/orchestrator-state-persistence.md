# Orchestrator State Persistence - Resume After Crash

**Ticket:** [SDT1-66] Orchestrator state persistence - resume after crash

## Overview

The Sprint Orchestrator now includes comprehensive state persistence and crash recovery capabilities. This feature allows the orchestrator to:

- ✅ Persist execution state after each ticket completion
- ✅ Resume interrupted sprints from the last checkpoint
- ✅ Recover from crashes, failures, or manual interruptions
- ✅ Track detailed execution progress and history
- ✅ Manage multiple concurrent sprint executions

## Architecture

### Components

1. **OrchestratorState Model** (`uat/backend/models.py`)
   - Database model for persisting execution state
   - Tracks ticket queue, completed tickets, failed tickets
   - Stores checkpoint timestamps and error information

2. **StateManager** (`agents/orchestrator_state.py`)
   - Core state management logic
   - CRUD operations for orchestrator state
   - Checkpoint and recovery methods

3. **Orchestrator** (`agents/orchestrator.py`)
   - Main orchestration logic
   - Integrates with StateManager for persistence
   - Implements resume capability

4. **API Router** (`uat/backend/orchestrator_router.py`)
   - REST API endpoints for orchestrator management
   - Start, resume, pause, cancel operations
   - Progress tracking and status queries

5. **CLI Tool** (`agents/cli_orchestrator.py`)
   - Command-line interface for orchestrator management
   - Useful for manual intervention and monitoring

## Database Schema

### orchestrator_states Table

```sql
CREATE TABLE orchestrator_states (
    id UUID PRIMARY KEY,
    sprint_id INTEGER NOT NULL,
    sprint_name VARCHAR(255) NOT NULL,
    jira_project_key VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- PENDING, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED
    
    -- Execution state (JSON)
    ticket_queue JSON NOT NULL,      -- List of remaining ticket keys
    completed_tickets JSON NOT NULL,  -- List of completed ticket keys
    failed_tickets JSON NOT NULL,     -- List of failed tickets with error info
    current_ticket VARCHAR(50),       -- Currently executing ticket
    
    -- Metadata
    total_tickets INTEGER NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    last_checkpoint_at TIMESTAMP,
    error_message TEXT,
    
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

## API Reference

### Start Sprint Execution

Start a new sprint execution from the beginning.

```http
POST /api/orchestrator/start
Content-Type: application/json

{
  "sprint_id": 123,
  "sprint_name": "Sprint 1",
  "jira_project_key": "SDT1"
}
```

**Response:**
```json
{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "sprint_id": 123,
  "sprint_name": "Sprint 1",
  "status": "running",
  "message": "Sprint execution started successfully"
}
```

### Resume Sprint Execution

Resume a paused or failed sprint from the last checkpoint.

```http
POST /api/orchestrator/resume
Content-Type: application/json

{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "jira_project_key": "SDT1"
}
```

**Response:**
```json
{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "sprint_id": 123,
  "sprint_name": "Sprint 1",
  "status": "completed",
  "message": "Sprint execution resumed successfully"
}
```

### Get Execution Progress

Check the current execution status and progress.

```http
GET /api/orchestrator/progress/{state_id}?jira_project_key=SDT1
```

**Response:**
```json
{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "sprint_id": 123,
  "sprint_name": "Sprint 1",
  "status": "running",
  "total_tickets": 10,
  "completed_tickets": 7,
  "failed_tickets": 1,
  "remaining_tickets": 2,
  "current_ticket": "SDT1-8",
  "progress_percentage": 70.0,
  "started_at": "2024-01-15T10:00:00Z",
  "last_checkpoint": "2024-01-15T10:45:00Z"
}
```

### List Resumable Sprints

Get all sprints that can be resumed (PAUSED or FAILED status).

```http
GET /api/orchestrator/resumable?jira_project_key=SDT1
```

**Response:**
```json
{
  "sprints": [
    {
      "state_id": "550e8400-e29b-41d4-a716-446655440000",
      "sprint_id": 123,
      "sprint_name": "Sprint 1",
      "status": "paused",
      "total_tickets": 10,
      "completed": 7,
      "failed": 1,
      "remaining": 2,
      "last_updated": "2024-01-15T10:45:00Z"
    }
  ],
  "count": 1
}
```

### Pause Sprint Execution

Pause a running sprint execution.

```http
POST /api/orchestrator/pause
Content-Type: application/json

{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "jira_project_key": "SDT1",
  "reason": "Manual pause for maintenance"
}
```

### Cancel Sprint Execution

Cancel a sprint execution (cannot be resumed).

```http
POST /api/orchestrator/cancel
Content-Type: application/json

{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "jira_project_key": "SDT1",
  "reason": "Sprint scope changed"
}
```

## CLI Reference

### Start Sprint

```bash
python agents/cli_orchestrator.py start \
  --sprint-id 123 \
  --sprint-name "Sprint 1" \
  --project SDT1 \
  --verbose
```

### Resume Sprint

```bash
python agents/cli_orchestrator.py resume \
  --state-id 550e8400-e29b-41d4-a716-446655440000 \
  --project SDT1 \
  --verbose
```

### List Resumable Sprints

```bash
python agents/cli_orchestrator.py list-resumable --project SDT1
```

Output:
```
Resumable sprints (2):

  PAUSED Sprint 1
    State ID:    550e8400-e29b-41d4-a716-446655440000
    Sprint ID:   123
    Total:       10 tickets
    Completed:   7
    Failed:      1
    Remaining:   2
    Last Update: 2024-01-15T10:45:00Z

    Resume with:
      python agents/cli_orchestrator.py resume --state-id 550e8400-e29b-41d4-a716-446655440000 --project SDT1
```

### Check Progress

```bash
python agents/cli_orchestrator.py progress \
  --state-id 550e8400-e29b-41d4-a716-446655440000 \
  --project SDT1
```

Output:
```
Sprint Execution Progress:

  Sprint:           Sprint 1 (ID: 123)
  State ID:         550e8400-e29b-41d4-a716-446655440000
  Status:           RUNNING

  Total Tickets:    10
  Completed:        7
  Failed:           1
  Remaining:        2
  Progress:         70.0%

  Current Ticket:   SDT1-8

  Started:          2024-01-15T10:00:00Z
  Last Checkpoint:  2024-01-15T10:45:00Z

  [████████████████████████████░░░░░░░░░░░░] 70.0%
```

### Pause Sprint

```bash
python agents/cli_orchestrator.py pause \
  --state-id 550e8400-e29b-41d4-a716-446655440000 \
  --project SDT1 \
  --reason "Manual maintenance"
```

### Cancel Sprint

```bash
python agents/cli_orchestrator.py cancel \
  --state-id 550e8400-e29b-41d4-a716-446655440000 \
  --project SDT1 \
  --reason "Sprint scope changed" \
  --force
```

## Recovery Scenarios

### Scenario 1: Server Crash During Execution

**Problem:** The orchestrator server crashes while executing ticket SDT1-5 in a 10-ticket sprint.

**Recovery:**

1. Restart the orchestrator service
2. List resumable sprints:
   ```bash
   python agents/cli_orchestrator.py list-resumable --project SDT1
   ```
3. Note the state_id of the interrupted sprint
4. Resume execution:
   ```bash
   python agents/cli_orchestrator.py resume \
     --state-id <state-id> \
     --project SDT1
   ```

**Result:** Orchestrator resumes from the last checkpoint, re-executes the current ticket if needed, and continues with remaining tickets.

### Scenario 2: Ticket Execution Failure

**Problem:** Ticket SDT1-7 fails due to a test failure or deployment issue.

**Behavior:**
- Orchestrator marks SDT1-7 as failed
- Stores error details in `failed_tickets`
- Continues executing remaining tickets (SDT1-8, SDT1-9, SDT1-10)
- Sprint completes with status COMPLETED but includes failed tickets

**Recovery:**
- Review failed tickets via API or CLI
- Fix the underlying issue
- Manually re-execute failed tickets or create a new sprint

### Scenario 3: Manual Pause for Maintenance

**Use Case:** Need to perform maintenance on infrastructure during sprint execution.

**Process:**

1. Pause the sprint:
   ```bash
   python agents/cli_orchestrator.py pause \
     --state-id <state-id> \
     --project SDT1 \
     --reason "Infrastructure maintenance"
   ```

2. Perform maintenance work

3. Resume when ready:
   ```bash
   python agents/cli_orchestrator.py resume \
     --state-id <state-id> \
     --project SDT1
   ```

### Scenario 4: Database Connection Loss

**Problem:** Database connection is lost during execution.

**Behavior:**
- StateManager operations will fail with database errors
- Orchestrator will mark execution as FAILED
- Last successful checkpoint is preserved in database

**Recovery:**

1. Restore database connectivity
2. Resume from last checkpoint:
   ```bash
   python agents/cli_orchestrator.py resume \
     --state-id <state-id> \
     --project SDT1
   ```

## State Transitions

```
┌─────────┐
│ PENDING │ ──start──> ┌─────────┐
└─────────┘            │ RUNNING │
                       └─────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
   ┌────────┐         ┌───────────┐       ┌──────────┐
   │ PAUSED │         │ COMPLETED │       │  FAILED  │
   └────────┘         └───────────┘       └──────────┘
        │                                       │
        │                                       │
        └──────────resume───────────────────────┘
                           │
                           ▼
                      ┌─────────┐
                      │ RUNNING │
                      └─────────┘

   ┌───────────┐
   │ CANCELLED │ (terminal state - cannot resume)
   └───────────┘
```

## Implementation Details

### Checkpoint Frequency

Checkpoints are saved:
- After each ticket completion (success or failure)
- When execution is paused
- Before executing each new ticket (current_ticket update)

### Error Handling

- **Ticket Execution Errors:** Caught and stored in `failed_tickets`, execution continues
- **System Errors:** Cause state to transition to FAILED, execution stops
- **Database Errors:** Propagated immediately, last checkpoint preserved

### Concurrency

- Multiple sprints can execute concurrently
- Each sprint has a unique `state_id`
- Database transactions ensure state consistency

### Performance

- Minimal overhead: ~10ms per checkpoint on typical PostgreSQL setup
- JSON fields allow flexible state storage without schema changes
- Indexed queries for fast resumable sprint lookups

## Testing

### Unit Tests

```bash
# Test state management
pytest uat/backend/tests/test_orchestrator_state.py

# Test orchestrator logic
pytest uat/backend/tests/test_orchestrator.py

# Test API endpoints
pytest uat/backend/tests/test_orchestrator_router.py
```

### Integration Tests

```bash
# Test full orchestration flow with resume
pytest uat/backend/tests/test_orchestrator.py::test_resume_sprint

# Test checkpoint persistence
pytest uat/backend/tests/test_orchestrator.py::test_checkpoint_during_execution
```

## Migration

If upgrading from a version without state persistence:

1. Run database migration:
   ```bash
   alembic upgrade head
   ```

2. The `orchestrator_states` table will be created automatically

3. Existing orchestrator code will work without changes

4. To enable resume capability, update code to use `Orchestrator.start_sprint()` and `Orchestrator.resume_sprint()`

## Monitoring and Observability

### Log Messages

The orchestrator logs key events:
- `[ORCHESTRATOR] Starting sprint: <name> (ID: <id>)`
- `[ORCHESTRATOR] Processing ticket: <key>`
- `[ORCHESTRATOR] ✓ Completed: <key>`
- `[ORCHESTRATOR] ✗ Failed: <key> - <error>`
- `[ORCHESTRATOR] Resuming sprint: <name> (state: <id>)`

### Database Queries

Monitor orchestrator state:
```sql
-- Active executions
SELECT * FROM orchestrator_states WHERE status = 'running';

-- Recent completions
SELECT * FROM orchestrator_states 
WHERE status = 'completed' 
ORDER BY completed_at DESC 
LIMIT 10;

-- Failed executions needing attention
SELECT * FROM orchestrator_states 
WHERE status = 'failed' 
ORDER BY updated_at DESC;
```

## Best Practices

1. **Always use resume for long-running sprints** to enable crash recovery
2. **Monitor checkpoint frequency** to ensure state is being saved
3. **Set up alerts** for FAILED status states
4. **Regularly clean up old states** to prevent database bloat
5. **Use meaningful sprint names** for easier identification during recovery
6. **Document manual interventions** in the pause/cancel reason field

## Troubleshooting

### Resume fails with "Cannot resume state with status COMPLETED"

**Cause:** Trying to resume a sprint that already finished.

**Solution:** Check state status with `list-resumable` or `progress` commands.

### Resume fails with "State not found"

**Cause:** Invalid state_id or state was deleted.

**Solution:** Use `list-resumable` to get valid state IDs.

### Tickets are re-executed after resume

**Cause:** Current ticket was not completed before crash.

**Solution:** This is expected behavior. The orchestrator will re-execute the current ticket to ensure completion.

### Progress shows 0% but tickets are completed

**Cause:** total_tickets not set correctly or tickets were added after start.

**Solution:** Ensure all tickets are known at sprint start time.

## Future Enhancements

- [ ] Support for concurrent ticket execution (parallel processing)
- [ ] Automatic retry logic for failed tickets
- [ ] Webhook notifications for state changes
- [ ] Historical analytics dashboard
- [ ] Automatic cleanup of old states
- [ ] Distributed orchestration across multiple workers

## Related Documentation

- [Orchestrator Architecture](./orchestrator-architecture.md)
- [Database Schema](./database-schema.md)
- [API Reference](./api-reference.md)
- [Deployment Guide](./deployment-guide.md)
