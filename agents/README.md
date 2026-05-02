# Virtual Dev Team Agents

This directory contains the autonomous agents that power the SynPro Virtual Dev Team.

## Overview

The Virtual Dev Team uses a multi-agent architecture with specialized agents for different roles:

- **PM Agent**: Product management, sprint planning, ticket creation
- **Dev Agent**: Code implementation, pull requests, code reviews
- **QA Agent**: Test creation, test execution, bug reporting
- **Manager Agent**: Sprint orchestration, resource allocation, progress tracking
- **Orchestrator**: Coordinates agent execution and manages sprint workflow

## Orchestrator

The Orchestrator is the central coordinator that:

1. Sequences tickets by execution order (from Jira `customfield_10071`)
2. Assigns tickets to appropriate agents
3. Monitors execution progress
4. Persists state for crash recovery
5. Handles failures gracefully

### Key Features

- **State Persistence**: All execution state saved to database
- **Resume Capability**: Continue from last checkpoint after crashes
- **Progress Tracking**: Real-time monitoring of sprint progress
- **Failure Handling**: Detailed tracking of failed tickets
- **Multiple Interfaces**: CLI, REST API, and Python API

### Quick Start

#### Start a Sprint

```bash
# CLI
python -m agents.cli start --sprint-id 123 --sprint-name "Sprint 42" --project SDT1

# Python
from agents.orchestrator import start_sprint_execution

state_id = start_sprint_execution(
    sprint_id=123,
    sprint_name="Sprint 42",
    jira_project_key="SDT1",
)
```

#### Resume After Interruption

```bash
# List resumable sprints
python -m agents.cli list-resumable

# Resume execution
python -m agents.cli resume --state-id <uuid> --project SDT1
```

#### Check Progress

```bash
python -m agents.cli progress --state-id <uuid>
```

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Orchestrator                         │
│                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────┐ │
│  │ State Manager│────▶│   Database   │◀────│ Checkpoint │ │
│  └──────────────┘     └──────────────┘     └────────────┘ │
│         │                                         ▲        │
│         ▼                                         │        │
│  ┌──────────────────────────────────────────────┐│        │
│  │          Sprint Execution Engine              ││        │
│  │                                               ││        │
│  │  1. Fetch tickets from Jira                  ││        │
│  │  2. Sort by execution_order                  ││        │
│  │  3. Execute sequentially                     ││        │
│  │  4. Save state after each ticket ────────────┘│        │
│  └──────────────────────────────────────────────┘         │
│         │                                                  │
│         ▼                                                  │
│  ┌────────────────┐  ┌────────────┐  ┌─────────────┐     │
│  │   Dev Agent    │  │  QA Agent  │  │ Other Agents│     │
│  └────────────────┘  └────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### State Persistence

The orchestrator persists state to the `orchestrator_states` table:

```python
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "sprint_id": 123,
    "sprint_name": "Sprint 42",
    "status": "running",
    "ticket_queue": ["SDT1-104", "SDT1-105"],
    "completed_tickets": ["SDT1-101", "SDT1-102", "SDT1-103"],
    "failed_tickets": [],
    "current_ticket": "SDT1-104",
    "total_tickets": 5,
    "progress": 60.0
}
```

### Status States

- **PENDING**: Created but not started
- **RUNNING**: Currently executing
- **PAUSED**: Manually paused (resumable)
- **COMPLETED**: Successfully completed
- **FAILED**: Failed with error (resumable)
- **CANCELLED**: Cancelled by user

### CLI Commands

| Command | Description |
|---------|-------------|
| `start` | Start sprint execution |
| `resume` | Resume paused/failed sprint |
| `list-resumable` | List sprints that can be resumed |
| `progress` | Show execution progress |
| `pause` | Pause running sprint |
| `cancel` | Cancel sprint execution |

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/orchestrator/start` | POST | Start sprint execution |
| `/api/orchestrator/resume` | POST | Resume paused/failed sprint |
| `/api/orchestrator/progress/{state_id}` | GET | Get progress |
| `/api/orchestrator/resumable` | GET | List resumable sprints |
| `/api/orchestrator/pause` | POST | Pause execution |
| `/api/orchestrator/cancel` | POST | Cancel execution |

## State Manager

The `StateManager` class handles all state persistence operations:

```python
from agents.orchestrator_state import StateManager

with StateManager() as state_manager:
    # Create state
    state = state_manager.create_state(
        sprint_id=123,
        sprint_name="Sprint 42",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1", "SDT1-2"],
    )
    
    # Mark tickets
    state_manager.mark_ticket_completed(state.id, "SDT1-1")
    state_manager.mark_ticket_failed(state.id, "SDT1-2", "Error message")
    
    # Checkpoint
    state_manager.checkpoint(state.id, current_ticket="SDT1-3")
    
    # Get progress
    progress = state_manager.get_progress(state.id)
```

## Examples

See `/examples/orchestrator_resume_example.py` for comprehensive examples:

- Basic sprint execution
- Resume after crash
- Manual pause/resume
- Progress monitoring
- Failure handling

## Documentation

- [Orchestrator Resume Guide](../docs/orchestrator-resume.md) - Comprehensive guide
- [API Reference](../docs/api-reference.md) - REST API documentation
- [Database Schema](../docs/database-schema.md) - Database design

## Testing

Run tests:

```bash
# All orchestrator tests
pytest uat/backend/tests/test_orchestrator.py -v

# State manager tests
pytest uat/backend/tests/test_orchestrator.py::test_resume_sprint -v

# API tests
pytest uat/backend/tests/test_orchestrator_router.py -v
```

## Development

### Adding New Agent Types

1. Create agent class in `agents/<agent_name>.py`
2. Implement `execute_ticket(ticket_key)` method
3. Register with orchestrator in ticket execution logic
4. Add tests in `uat/backend/tests/test_<agent_name>.py`

### Extending State Persistence

To add new state fields:

1. Add column to `OrchestratorState` model in `uat/backend/models.py`
2. Create Alembic migration
3. Update `StateManager` methods as needed
4. Update API response models in `uat/backend/orchestrator_router.py`

## Troubleshooting

### Database Connection Issues

Ensure `DATABASE_URL` is set:

```bash
export DATABASE_URL="postgresql://user:password@host:5432/database"
```

### State Not Found

List all states:

```bash
python -m agents.cli list-resumable
```

Query database:

```sql
SELECT id, sprint_name, status FROM orchestrator_states ORDER BY updated_at DESC;
```

### Performance Issues

For large sprints (>100 tickets), consider:

- Batching checkpoints (save every N tickets)
- Using database connection pooling
- Running orchestrator on dedicated infrastructure

## Contributing

When contributing to the orchestrator:

1. Add type hints to all functions
2. Write comprehensive docstrings
3. Add tests for new functionality
4. Update documentation
5. Ensure backward compatibility with existing states

## License

Copyright SynPro - Proprietary and Confidential
