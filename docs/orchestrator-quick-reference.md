# Orchestrator State Persistence - Quick Reference

**Ticket:** [SDT1-66]

## Quick Commands

### Start a Sprint
```bash
python agents/orchestrator_cli.py start \
  --sprint-id 42 \
  --sprint-name "Sprint 10" \
  --project SDT1
```

### List Resumable States
```bash
python agents/orchestrator_cli.py list-resumable
```

### Check Progress
```bash
python agents/orchestrator_cli.py progress --state-id <uuid>
```

### Resume Execution
```bash
python agents/orchestrator_cli.py resume \
  --state-id <uuid> \
  --project SDT1
```

### Pause Execution
```bash
python agents/orchestrator_cli.py pause \
  --state-id <uuid> \
  --reason "Optional reason"
```

### Cancel Execution
```bash
python agents/orchestrator_cli.py cancel \
  --state-id <uuid> \
  --reason "Optional reason" \
  --yes
```

## API Quick Reference

### Start Sprint
```http
POST /api/orchestrator/start
Authorization: Bearer <token>

{
  "sprint_id": 42,
  "sprint_name": "Sprint 10",
  "jira_project_key": "SDT1"
}
```

### Resume Sprint
```http
POST /api/orchestrator/resume
Authorization: Bearer <token>

{
  "state_id": "550e8400-e29b-41d4-a716-446655440000",
  "jira_project_key": "SDT1"
}
```

### Check Progress
```http
GET /api/orchestrator/progress/{state_id}
Authorization: Bearer <token>
```

### List Resumable
```http
GET /api/orchestrator/resumable
Authorization: Bearer <token>
```

## Python Quick Reference

### Start Sprint
```python
from agents.orchestrator import start_sprint_execution

state_id = start_sprint_execution(
    sprint_id=42,
    sprint_name="Sprint 10",
    jira_project_key="SDT1",
    verbose=True,
)
```

### Resume Sprint
```python
from agents.orchestrator import resume_sprint_execution

resume_sprint_execution(
    state_id=state_id,
    jira_project_key="SDT1",
    verbose=True,
)
```

### Check Progress
```python
from agents.orchestrator_state import StateManager

with StateManager() as sm:
    progress = sm.get_progress(state_id)
    print(f"Progress: {progress['progress_percentage']}%")
```

## State Statuses

| Status | Description | Can Resume? |
|--------|-------------|-------------|
| `PENDING` | Created, not started | No |
| `RUNNING` | Currently executing | No |
| `PAUSED` | Manually paused | **Yes** |
| `FAILED` | Failed/crashed | **Yes** |
| `COMPLETED` | Successfully finished | No |
| `CANCELLED` | Permanently cancelled | No |

## Common Workflows

### Crash Recovery
1. List resumable states: `orchestrator_cli.py list-resumable`
2. Find your state ID
3. Resume: `orchestrator_cli.py resume --state-id <uuid> --project SDT1`

### Scheduled Maintenance
1. Pause: `orchestrator_cli.py pause --state-id <uuid> --reason "Maintenance"`
2. Perform maintenance
3. Resume: `orchestrator_cli.py resume --state-id <uuid> --project SDT1`

### Monitor Long-Running Sprint
```bash
# Check progress periodically
watch -n 30 'python agents/orchestrator_cli.py progress --state-id <uuid>'
```

## Files Reference

| File | Purpose |
|------|---------|
| `agents/orchestrator.py` | Main orchestrator |
| `agents/orchestrator_state.py` | State management |
| `agents/orchestrator_cli.py` | CLI tool |
| `uat/backend/orchestrator_router.py` | REST API |
| `uat/backend/models.py` | Database models |
| `uat/backend/test_orchestrator_state.py` | Unit tests |
| `uat/backend/test_orchestrator_integration.py` | Integration tests |
| `examples/orchestrator_resume_demo.py` | Demo script |

## Testing

### Run Unit Tests
```bash
cd uat/backend
pytest test_orchestrator_state.py -v
```

### Run Integration Tests
```bash
cd uat/backend
pytest test_orchestrator_integration.py -v
```

### Run Demo
```bash
python examples/orchestrator_resume_demo.py
```

## Troubleshooting

### "State not found"
- Verify state ID with `list-resumable`
- Check you're using the correct database

### "Cannot resume state with status X"
- Only PAUSED or FAILED states can be resumed
- Check status with `progress` command

### Database connection issues
- Ensure `DATABASE_URL` environment variable is set
- Verify database is accessible

## Need More Info?

See full documentation: `docs/orchestrator-state-persistence.md`
