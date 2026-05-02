# Orchestrator Setup Guide

This guide walks through setting up the orchestrator with state persistence for production use.

## Prerequisites

- PostgreSQL 12+ (recommended) or SQLite for development
- Python 3.11+
- Database access credentials
- Jira API access

## Database Setup

### Option 1: PostgreSQL (Production)

1. **Create Database**

```sql
CREATE DATABASE synpro_dev_team;
CREATE USER synpro_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE synpro_dev_team TO synpro_user;
```

2. **Set Environment Variable**

```bash
export DATABASE_URL="postgresql://synpro_user:your_secure_password@localhost:5432/synpro_dev_team"
```

3. **Initialize Tables**

```bash
cd uat/backend
python -c "from database import init_database; init_database()"
```

### Option 2: SQLite (Development)

1. **Set Environment Variable**

```bash
export DATABASE_URL="sqlite:///./synpro_dev_team.db"
```

2. **Initialize Tables**

```bash
cd uat/backend
python -c "from database import init_database; init_database()"
```

## Database Schema

The orchestrator creates the `orchestrator_states` table:

```sql
CREATE TABLE orchestrator_states (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sprint_id           INTEGER NOT NULL,
    sprint_name         VARCHAR(255) NOT NULL,
    jira_project_key    VARCHAR(50) NOT NULL,
    status              VARCHAR(20) NOT NULL,
    ticket_queue        JSON NOT NULL,
    completed_tickets   JSON NOT NULL,
    failed_tickets      JSON NOT NULL,
    current_ticket      VARCHAR(50),
    total_tickets       INTEGER NOT NULL,
    started_at          TIMESTAMP WITH TIME ZONE,
    completed_at        TIMESTAMP WITH TIME ZONE,
    last_checkpoint_at  TIMESTAMP WITH TIME ZONE,
    error_message       TEXT,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_orchestrator_states_sprint_id ON orchestrator_states(sprint_id);
CREATE INDEX idx_orchestrator_states_status ON orchestrator_states(status);
CREATE INDEX idx_orchestrator_states_updated_at ON orchestrator_states(updated_at DESC);
```

### Manual Creation (if needed)

If automatic creation fails, you can create the table manually:

```bash
psql -U synpro_user -d synpro_dev_team -f scripts/create_orchestrator_tables.sql
```

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Database
DATABASE_URL=postgresql://synpro_user:password@localhost:5432/synpro_dev_team

# Jira
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your_jira_api_token

# GitHub
GITHUB_TOKEN=your_github_token
GITHUB_REPO=your-org/your-repo

# Optional: Logging
LOG_LEVEL=INFO
```

Load environment variables:

```bash
source .env
# Or use python-dotenv in your code
```

### Jira Custom Fields

Ensure your Jira project has the required custom fields:

- **execution_order** (`customfield_10071`): Integer field for ticket sequencing
- **story_points** (`customfield_10016`): Integer field for estimation

Verify custom fields in Jira:

```python
from jira import JIRA

jira = JIRA(server=JIRA_URL, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN))
issue = jira.issue("SDT1-1")
print(issue.raw["fields"]["customfield_10071"])  # execution_order
```

## Installation

### 1. Install Dependencies

```bash
cd uat/backend
pip install -r requirements.txt
```

Required packages:
- `sqlalchemy>=2.0.0`
- `psycopg2-binary>=2.9.0` (for PostgreSQL)
- `fastapi>=0.104.0`
- `uvicorn>=0.24.0`

### 2. Verify Installation

```bash
# Test database connection
python -c "from database import SessionLocal; db = SessionLocal(); print('✓ Database connected')"

# Test orchestrator import
python -c "from agents.orchestrator import Orchestrator; print('✓ Orchestrator imported')"

# Run tests
pytest uat/backend/tests/test_orchestrator.py -v
```

## Running the Orchestrator

### CLI Usage

1. **Start a Sprint**

```bash
python -m agents.cli start \
    --sprint-id 123 \
    --sprint-name "Sprint 42" \
    --project SDT1
```

2. **Monitor Progress**

```bash
# Get state ID from start command output
export STATE_ID="550e8400-e29b-41d4-a716-446655440000"

# Check progress
python -m agents.cli progress --state-id $STATE_ID
```

3. **Resume After Interruption**

```bash
# List resumable sprints
python -m agents.cli list-resumable

# Resume specific sprint
python -m agents.cli resume --state-id $STATE_ID --project SDT1
```

### API Server

1. **Start the API Server**

```bash
cd uat/backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

2. **Access API Documentation**

Navigate to: http://localhost:8000/docs

3. **Test API Endpoints**

```bash
# Start sprint
curl -X POST http://localhost:8000/api/orchestrator/start \
  -H "Content-Type: application/json" \
  -d '{
    "sprint_id": 123,
    "sprint_name": "Sprint 42",
    "jira_project_key": "SDT1"
  }'

# Check progress
curl http://localhost:8000/api/orchestrator/progress/{state_id}

# List resumable
curl http://localhost:8000/api/orchestrator/resumable
```

### Python API

```python
from agents.orchestrator import start_sprint_execution, resume_sprint_execution

# Start sprint
state_id = start_sprint_execution(
    sprint_id=123,
    sprint_name="Sprint 42",
    jira_project_key="SDT1",
)

print(f"Started sprint with state ID: {state_id}")

# Resume later if needed
resume_sprint_execution(state_id, jira_project_key="SDT1")
```

## Monitoring

### Database Queries

**Active Sprints**:

```sql
SELECT id, sprint_name, status, current_ticket, 
       (SELECT COUNT(*) FROM jsonb_array_elements_text(completed_tickets)) as completed,
       (SELECT COUNT(*) FROM jsonb_array_elements_text(ticket_queue)) as remaining
FROM orchestrator_states
WHERE status = 'running'
ORDER BY started_at DESC;
```

**Recent Failures**:

```sql
SELECT id, sprint_name, error_message, updated_at
FROM orchestrator_states
WHERE status = 'failed'
ORDER BY updated_at DESC
LIMIT 10;
```

**Progress Summary**:

```sql
SELECT 
    status,
    COUNT(*) as count,
    AVG(total_tickets) as avg_tickets,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at)) / 3600) as avg_hours
FROM orchestrator_states
WHERE started_at IS NOT NULL
GROUP BY status;
```

### Logging

Configure logging in `uat/backend/main.py`:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler()
    ]
)
```

## Backup and Recovery

### Backup State Data

```bash
# Backup orchestrator states
pg_dump -U synpro_user -d synpro_dev_team -t orchestrator_states > orchestrator_backup.sql

# Or backup entire database
pg_dump -U synpro_user synpro_dev_team > full_backup.sql
```

### Restore State Data

```bash
psql -U synpro_user -d synpro_dev_team < orchestrator_backup.sql
```

### Export State as JSON

```python
from agents.orchestrator_state import StateManager
import json

with StateManager() as state_manager:
    state = state_manager.get_state(state_id)
    
    state_data = {
        "id": str(state.id),
        "sprint_id": state.sprint_id,
        "sprint_name": state.sprint_name,
        "status": state.status.value,
        "ticket_queue": state.ticket_queue,
        "completed_tickets": state.completed_tickets,
        "failed_tickets": state.failed_tickets,
    }
    
    with open(f"state_backup_{state.id}.json", "w") as f:
        json.dump(state_data, f, indent=2)
```

## Performance Tuning

### Database Optimization

1. **Connection Pooling**

```python
# In database.py
engine = create_engine(
    database_url,
    pool_size=20,          # Increased for high concurrency
    max_overflow=40,       # Additional connections if needed
    pool_pre_ping=True,    # Verify connections before use
    pool_recycle=3600,     # Recycle connections every hour
)
```

2. **Indexes**

```sql
-- Add indexes for common queries
CREATE INDEX idx_orchestrator_states_project ON orchestrator_states(jira_project_key);
CREATE INDEX idx_orchestrator_states_current_ticket ON orchestrator_states(current_ticket);
```

3. **Vacuum and Analyze** (PostgreSQL)

```bash
# Schedule regular maintenance
psql -U synpro_user -d synpro_dev_team -c "VACUUM ANALYZE orchestrator_states;"
```

### Application Optimization

1. **Checkpoint Batching** (for large sprints)

```python
# In orchestrator.py, modify _execute_sprint
# Save state every N tickets instead of every ticket
CHECKPOINT_INTERVAL = 5

if len(state.completed_tickets) % CHECKPOINT_INTERVAL == 0:
    self.state_manager.checkpoint(state_id, ...)
```

2. **Async Execution** (advanced)

For concurrent ticket execution:

```python
import asyncio

async def execute_tickets_concurrently(tickets):
    tasks = [execute_ticket(t) for t in tickets]
    results = await asyncio.gather(*tasks)
    return results
```

## Troubleshooting

### Common Issues

**1. Database Connection Failed**

```
Error: could not connect to server
```

Solution:
- Verify DATABASE_URL is correct
- Check PostgreSQL is running: `pg_isready`
- Verify firewall rules allow connection
- Check credentials: `psql -U synpro_user -d synpro_dev_team`

**2. Table Does Not Exist**

```
Error: relation "orchestrator_states" does not exist
```

Solution:
```bash
python -c "from database import init_database; init_database()"
```

**3. State Not Found**

```
Error: State {uuid} not found
```

Solution:
```bash
# List all states
python -c "
from database import SessionLocal
from models import OrchestratorState
db = SessionLocal()
states = db.query(OrchestratorState).all()
for s in states:
    print(f'{s.id}: {s.sprint_name} - {s.status.value}')
"
```

**4. JSON Decode Error**

```
Error: could not decode JSON value
```

Solution:
- Ensure PostgreSQL JSON/JSONB support is enabled
- For SQLite, ensure version supports JSON1 extension
- Verify data integrity in failed_tickets/completed_tickets fields

### Debug Mode

Enable verbose logging:

```bash
# CLI
python -m agents.cli start --sprint-id 123 --sprint-name "Sprint" --project SDT1 --verbose

# Python
orchestrator = Orchestrator("SDT1", verbose=True)
```

## Production Deployment

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "uat.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: synpro_dev_team
      POSTGRES_USER: synpro_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://synpro_user:${DB_PASSWORD}@db:5432/synpro_dev_team
      JIRA_URL: ${JIRA_URL}
      JIRA_EMAIL: ${JIRA_EMAIL}
      JIRA_API_TOKEN: ${JIRA_API_TOKEN}
    depends_on:
      - db

volumes:
  postgres_data:
```

Deploy:

```bash
docker-compose up -d
```

### Kubernetes Deployment

See `k8s/orchestrator-deployment.yaml` for Kubernetes manifests.

## Security

### Database Security

1. **Use Strong Passwords**

```bash
# Generate secure password
openssl rand -base64 32
```

2. **Restrict Database Access**

```sql
-- Revoke public access
REVOKE ALL ON DATABASE synpro_dev_team FROM PUBLIC;

-- Grant only to specific user
GRANT CONNECT ON DATABASE synpro_dev_team TO synpro_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO synpro_user;
```

3. **Enable SSL**

```python
# In database.py
engine = create_engine(
    database_url,
    connect_args={
        "sslmode": "require",
        "sslcert": "/path/to/client-cert.pem",
        "sslkey": "/path/to/client-key.pem",
        "sslrootcert": "/path/to/ca-cert.pem",
    }
)
```

### API Security

1. **Add Authentication**

```python
# In orchestrator_router.py
from fastapi import Depends, HTTPException
from auth import get_current_user

@router.post("/start")
async def start_sprint(
    request: StartSprintRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Only authenticated users can start sprints
    ...
```

2. **Rate Limiting**

Already configured in `main.py` with `slowapi`.

## Support

For issues or questions:

1. Check logs: `orchestrator.log`
2. Review database state
3. Run diagnostics: `python -m agents.cli list-resumable`
4. Contact DevOps team

## Next Steps

- Set up monitoring dashboard
- Configure automated backups
- Implement alerting for failed sprints
- Integrate with CI/CD pipeline
- Add webhooks for sprint events
