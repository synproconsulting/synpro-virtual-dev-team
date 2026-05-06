# Orchestrator State Persistence - Resume After Crash

## Overview

The orchestrator state persistence feature enables the sprint orchestrator to resume execution after interruptions, failures, or manual pauses. All execution state is persisted to the database, allowing seamless recovery without losing progress.

## Architecture

### Backend Components

1. **Database Model** (`uat/backend/models.py`)
   - `OrchestratorState` table stores execution state
   - Fields include: sprint info, status, ticket queues, completed/failed lists, timestamps
   - `OrchestratorStatus` enum: PENDING, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED

2. **State Manager** (`agents/orchestrator_state.py`)
   - Manages CRUD operations for orchestrator states
   - Provides checkpoint/resume functionality
   - Handles ticket completion and failure tracking

3. **Orchestrator** (`agents/orchestrator.py`)
   - Main sprint execution engine
   - Uses StateManager for persistence
   - Supports start/resume/pause/cancel operations

4. **API Router** (`uat/backend/orchestrator_router.py`)
   - REST API endpoints for state management
   - Authentication required for all endpoints
   - Exposes start, resume, pause, cancel, progress, and list operations

### Frontend Components

1. **API Client** (`control-centre/src/api/orchestratorApi.js`)
   - JavaScript API wrapper for orchestrator endpoints
   - Handles authentication tokens
   - Error handling and response parsing

2. **Control Panel** (`control-centre/src/components/OrchestratorControl.jsx`)
   - React component for viewing and managing orchestrator states
   - Real-time progress monitoring
   - Resume/pause/cancel controls
   - Detailed state inspection with ticket lists

3. **App Integration** (`control-centre/src/App.jsx`)
   - New "Orchestrator" tab in control centre navigation
   - Integrated with existing sprint management interface

## API Endpoints

### Start Sprint
```http
POST /api/orchestrator/start
Content-Type: application/json
Authorization: Bearer <token>

{
  "sprint_id": 5,
  "sprint_name": "Sprint 5 - State Persistence",
  "jira_project_key": "SDT1"
}
```

**Response:**
```json
{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "sprint_id": 5,
  "sprint_name": "Sprint 5 - State Persistence",
  "status": "pending",
  "message": "Sprint execution initiated. 12 tickets queued. State ID: ..."
}
```

### Resume Sprint
```http
POST /api/orchestrator/resume
Content-Type: application/json
Authorization: Bearer <token>

{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "jira_project_key": "SDT1"
}
```

**Response:**
```json
{
  "message": "Sprint execution resumed. 8 tickets remaining.",
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running"
}
```

### Pause Sprint
```http
POST /api/orchestrator/pause
Content-Type: application/json
Authorization: Bearer <token>

{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "reason": "Manual pause for review"
}
```

### Cancel Sprint
```http
POST /api/orchestrator/cancel
Content-Type: application/json
Authorization: Bearer <token>

{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "reason": "Sprint cancelled - requirements changed"
}
```

### Get Progress
```http
GET /api/orchestrator/progress/{state_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "sprint_id": 5,
  "sprint_name": "Sprint 5 - State Persistence",
  "status": "running",
  "total_tickets": 12,
  "completed_tickets": 4,
  "failed_tickets": 1,
  "remaining_tickets": 7,
  "current_ticket": "SDT1-68",
  "progress_percentage": 33.33,
  "started_at": "2024-01-15T10:30:00Z",
  "last_checkpoint": "2024-01-15T11:45:00Z"
}
```

### Get Full State
```http
GET /api/orchestrator/state/{state_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "sprint_id": 5,
  "sprint_name": "Sprint 5 - State Persistence",
  "jira_project_key": "SDT1",
  "status": "running",
  "ticket_queue": ["SDT1-68", "SDT1-69", "SDT1-70"],
  "completed_tickets": ["SDT1-64", "SDT1-65", "SDT1-66", "SDT1-67"],
  "failed_tickets": [
    {
      "ticket_key": "SDT1-63",
      "error_message": "CI failed - tests did not pass",
      "timestamp": "2024-01-15T11:30:00Z"
    }
  ],
  "current_ticket": "SDT1-68",
  "total_tickets": 12,
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": null,
  "last_checkpoint_at": "2024-01-15T11:45:00Z",
  "error_message": null,
  "created_at": "2024-01-15T10:29:00Z",
  "updated_at": "2024-01-15T11:45:00Z"
}
```

### List Resumable States
```http
GET /api/orchestrator/resumable
Authorization: Bearer <token>
```

**Response:**
```json
{
  "states": [
    {
      "state_id": "550e8400-e29b-41d4-a716-446655440000",
      "sprint_id": 5,
      "sprint_name": "Sprint 5 - State Persistence",
      "status": "paused",
      "total_tickets": 12,
      "completed": 4,
      "failed": 1,
      "remaining": 7,
      "last_updated": "2024-01-15T11:45:00Z"
    }
  ],
  "count": 1
}
```

## Usage

### Starting a Sprint

```python
from agents.orchestrator import Orchestrator

# Start a new sprint execution
with Orchestrator("SDT1", verbose=True) as orchestrator:
    state_id = orchestrator.start_sprint(
        sprint_id=5,
        sprint_name="Sprint 5 - State Persistence"
    )
    print(f"Started sprint with state ID: {state_id}")
```

### Resuming After Interruption

```python
from uuid import UUID
from agents.orchestrator import Orchestrator

# Resume a paused or failed sprint
state_id = UUID("550e8400-e29b-41d4-a716-446655440000")

with Orchestrator("SDT1", verbose=True) as orchestrator:
    orchestrator.resume_sprint(state_id)
```

### Viewing Resumable States

```python
from agents.orchestrator import Orchestrator

with Orchestrator("SDT1") as orchestrator:
    resumable = orchestrator.list_resumable()
    for state in resumable:
        print(f"{state['sprint_name']}: {state['remaining']} tickets remaining")
```

## Frontend Usage

### Accessing the Control Panel

1. Navigate to Control Centre
2. Click the "Orchestrator" tab in the navigation bar
3. View all resumable sprint executions (paused or failed states)

### Resuming a Sprint

1. In the Orchestrator tab, locate the sprint you want to resume
2. Click the expand button (chevron icon) to view details
3. Review the current progress, completed tickets, and failed tickets
4. Click the "Resume" button
5. Monitor progress in real-time

### Pausing a Sprint

1. Find the running sprint in the list
2. Expand the state details
3. Click the "Pause" button
4. The sprint will pause after the current ticket completes

### Viewing Progress

The control panel provides:
- **Progress bar**: Visual representation of completion percentage
- **Ticket counts**: Completed, failed, and remaining tickets
- **Current ticket**: Currently executing ticket key
- **Ticket lists**: Detailed view of queue, completed, and failed tickets
- **Timestamps**: Started, last checkpoint, and completion times

## Error Handling

### Failed Tickets

When a ticket fails:
1. The error is logged with timestamp
2. The ticket is removed from the queue
3. The ticket is added to the failed_tickets list with error details
4. Execution continues with the next ticket

### Crash Recovery

If the orchestrator crashes:
1. All state is preserved in the database
2. The last checkpoint captures the execution position
3. Resume the sprint using the state_id
4. Execution continues from the last completed ticket

### Manual Intervention

Paused sprints require manual resume:
1. Review the state in the control panel
2. Check failed tickets and resolve issues
3. Click "Resume" to continue execution
4. Or click "Cancel" to abandon the sprint

## Database Schema

### orchestrator_states Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| sprint_id | Integer | Jira sprint ID |
| sprint_name | String | Sprint name |
| jira_project_key | String | Jira project key (e.g., 'SDT1') |
| status | Enum | PENDING, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED |
| ticket_queue | JSON | Array of ticket keys in execution order |
| completed_tickets | JSON | Array of completed ticket keys |
| failed_tickets | JSON | Array of objects with ticket_key, error_message, timestamp |
| current_ticket | String | Currently executing ticket key |
| total_tickets | Integer | Total number of tickets in sprint |
| started_at | Timestamp | When execution started |
| completed_at | Timestamp | When execution completed |
| last_checkpoint_at | Timestamp | Last state save time |
| error_message | Text | Error message if failed |
| created_at | Timestamp | Record creation time |
| updated_at | Timestamp | Record update time |

## Checkpointing Strategy

The orchestrator saves state at the following points:

1. **Sprint start**: Initial state created with ticket queue
2. **Before ticket execution**: Current ticket updated
3. **After ticket completion**: Ticket moved from queue to completed list
4. **After ticket failure**: Ticket moved to failed list with error
5. **On pause**: Status changed to PAUSED
6. **On completion**: Status changed to COMPLETED, completion time recorded

## Testing

### Manual Testing

1. Start a sprint with multiple tickets
2. Manually kill the orchestrator process during execution
3. Check the database for the saved state
4. Resume the sprint using the Control Centre
5. Verify execution continues from the last checkpoint

### Automated Testing

```python
# Test state persistence (example)
def test_orchestrator_resume():
    with Orchestrator("SDT1") as orch:
        # Start sprint
        state_id = orch.start_sprint(5, "Test Sprint")
        
        # Simulate interruption
        state = orch.state_manager.get_state(state_id)
        assert len(state.ticket_queue) > 0
        
        # Resume
        orch.resume_sprint(state_id)
        
        # Verify progress
        progress = orch.get_progress(state_id)
        assert progress["status"] == "running"
```

## Future Enhancements

1. **Background execution**: Move orchestrator to background workers
2. **Webhook notifications**: Alert on failures or completion
3. **Parallel execution**: Support concurrent ticket execution
4. **Auto-retry**: Automatically retry failed tickets
5. **State history**: Track state changes over time
6. **Export reports**: Generate execution reports in PDF/CSV

## Troubleshooting

### State Not Found
- Verify the state_id is correct
- Check if state was deleted from database
- Ensure database migrations are up to date

### Cannot Resume
- Check state status (only PAUSED and FAILED can be resumed)
- Verify authentication token is valid
- Check backend logs for errors

### Progress Not Updating
- Ensure orchestrator is actually running (not just state marked as running)
- Check for exceptions in orchestrator execution
- Verify database connection is active

### Missing Tickets
- Verify Jira connection and credentials
- Check execution_order (customfield_10071) is set on tickets
- Ensure tickets are in "To Do" status

## Related Documentation

- [Orchestrator Architecture](../agents/orchestrator.py)
- [State Manager](../agents/orchestrator_state.py)
- [Database Models](../uat/backend/models.py)
- [API Router](../uat/backend/orchestrator_router.py)
