# Orchestrator Setup Guide

This guide walks through setting up the Orchestrator with resume capability.

## Prerequisites

- Python 3.11+
- PostgreSQL database
- Jira instance with API access
- Environment variables configured

## Installation

### 1. Install Dependencies

```bash
cd uat/backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file or set environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Jira (if using Jira integration)
JIRA_URL=https://your-domain.atlassian.net
JIRA_USER_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=SDT1

# Claude API (for PM Agent)
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### 3. Run Database Migration

Create the `orchestrator_states` table:

```bash
cd uat/backend
python -m migrations.add_orchestrator_state
```

Verify the table was created:

```sql
-- In PostgreSQL
\d orchestrator_states
```

## Verification

### 1. Run Tests

```bash
cd uat/backend
pytest tests/test_orchestrator_state.py -v
pytest tests/test_orchestrator.py -v
pytest tests/test_orchestrator_integration.py -v
```

All tests should pass.

### 2. Run Demo

```bash
cd agents
python examples/orchestrator_demo.py
```

Follow the prompts to see the orchestrator in action.

### 3. Try CLI

```bash
# List resumable executions (should be empty initially)
python agents/orchestrator_cli.py list --project SDT1

# The demo will have created some states you can inspect
```

## Quick Start Usage

### Python API

```python
from agents.orchestrator import Orchestrator

# Start a sprint
with Orchestrator("SDT1", verbose=True) as orch:
    state_id = orch.start_sprint(
        sprint_id=123,
        sprint_name="Sprint 1",
    )
    print(f"State ID: {state_id}")

# Resume later
from uuid import UUID

state_id = UUID("...")  # From above
with Orchestrator("SDT1", verbose=True) as orch:
    orch.resume_sprint(state_id)
```

### CLI

```bash
# Start a sprint
python agents/orchestrator_cli.py start \
    --sprint-id 123 \
    --sprint-name "Sprint 1" \
    --project SDT1

# Check progress
python agents/orchestrator_cli.py progress \
    --state-id <uuid> \
    --project SDT1

# Resume if paused/failed
python agents/orchestrator_cli.py resume \
    --state-id <uuid> \
    --project SDT1
```

## Integration with PM Agent

### 1. PM Agent Creates Sprint

```python
from agents.pm_agent import build_pm_agent
from crewai import Crew, Task

pm = build_pm_agent()

task = Task(
    description="Create Sprint 1 with user authentication stories",
    expected_output="Sprint created with stories having execution_order set",
    agent=pm,
)

crew = Crew(agents=[pm], tasks=[task])
result = crew.kickoff()
```

### 2. Extract Sprint Info

From the PM Agent output, extract:
- Sprint ID
- Sprint name

### 3. Start Orchestrator

```python
from agents.orchestrator import Orchestrator

with Orchestrator("SDT1") as orch:
    state_id = orch.start_sprint(
        sprint_id=sprint_id,  # From PM Agent
        sprint_name=sprint_name,  # From PM Agent
    )
```

## Troubleshooting

### Database Connection Error

```
ValueError: DATABASE_URL environment variable is not set
```

**Solution**: Set `DATABASE_URL` environment variable:

```bash
export DATABASE_URL=postgresql://user:pass@localhost:5432/db
```

### Table Does Not Exist

```
sqlalchemy.exc.ProgrammingError: relation "orchestrator_states" does not exist
```

**Solution**: Run the migration:

```bash
cd uat/backend
python -m migrations.add_orchestrator_state
```

### Import Errors

```
ModuleNotFoundError: No module named 'agents'
```

**Solution**: Ensure you're running from the correct directory or add to PYTHONPATH:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### State Not Resumable

```
ValueError: Cannot resume state with status completed
```

**Solution**: Only PAUSED or FAILED states can be resumed. Check state status:

```bash
python agents/orchestrator_cli.py progress --state-id <uuid> --project SDT1
```

## Development Setup

### Running Tests with Coverage

```bash
cd uat/backend
pytest tests/test_orchestrator*.py --cov=agents --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html
```

### Database Reset

To reset the orchestrator_states table:

```bash
# Drop table
python -m migrations.add_orchestrator_state --downgrade

# Recreate table
python -m migrations.add_orchestrator_state
```

**Warning**: This deletes all orchestrator execution history.

### Debug Mode

Enable verbose logging:

```python
with Orchestrator("SDT1", verbose=True) as orch:
    # ... operations
```

Or via CLI:
```bash
# Default is verbose, use --quiet to disable
python agents/orchestrator_cli.py start \
    --sprint-id 123 \
    --sprint-name "Sprint 1" \
    --project SDT1
```

## Production Deployment

### Database Backup

Before deploying:

```bash
pg_dump -h localhost -U user -d dbname -t orchestrator_states > backup.sql
```

### Environment Variables

Set in production environment:
- `DATABASE_URL` - Production database URL
- `JIRA_URL`, `JIRA_USER_EMAIL`, `JIRA_API_TOKEN` - Jira credentials
- `ANTHROPIC_API_KEY` - Claude API key

### Monitoring

Monitor these metrics:
- Active orchestrator executions
- Ticket success/failure rates
- Average execution time per ticket
- Database connection pool usage

### Alerting

Set up alerts for:
- High failure rates
- Long-running executions (stuck)
- Database connection issues
- State corruption

## Next Steps

1. **Read Documentation**: See `docs/orchestrator_resume_capability.md`
2. **Review Examples**: Check `agents/examples/orchestrator_demo.py`
3. **Integrate with PM Agent**: Connect sprint planning to execution
4. **Add Monitoring**: Implement logging and metrics
5. **Test in Staging**: Verify with real sprints before production

## Support

For issues:
1. Check logs and error messages
2. Review state in database
3. Verify environment configuration
4. Check test results
5. Contact development team

## Useful Commands

```bash
# Check database connection
python -c "from uat.backend.database import engine; print(engine.connect())"

# List all states
python -c "from agents.orchestrator_state import StateManager; \
  with StateManager() as sm: \
    states = sm.db.query(models.OrchestratorState).all(); \
    print(f'{len(states)} states found')"

# Clean up completed states older than 30 days
# (Run in Python REPL or script)
from datetime import datetime, timedelta
from agents.orchestrator_state import StateManager
from models import OrchestratorState, OrchestratorStatus

with StateManager() as sm:
    cutoff = datetime.utcnow() - timedelta(days=30)
    old_states = sm.db.query(OrchestratorState).filter(
        OrchestratorState.status == OrchestratorStatus.COMPLETED,
        OrchestratorState.completed_at < cutoff
    ).all()
    print(f"Found {len(old_states)} old states to clean up")
    # Delete if desired
    # for state in old_states:
    #     sm.db.delete(state)
    # sm.db.commit()
```
