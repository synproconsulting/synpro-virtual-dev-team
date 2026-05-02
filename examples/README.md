# Orchestrator Examples

This directory contains example scripts and demonstrations for the Sprint Orchestrator with crash recovery capabilities.

## Examples

### orchestrator_crash_recovery_demo.py

A comprehensive demonstration of the orchestrator's crash recovery and state persistence features.

**Features Demonstrated:**
- Basic sprint execution with multiple tickets
- Crash simulation and recovery
- Ticket failure handling
- Listing resumable sprints
- Progress tracking

**Usage:**
```bash
python examples/orchestrator_crash_recovery_demo.py
```

**Output:**
The script will show:
1. Normal sprint execution completing all tickets
2. A simulated crash during execution, followed by successful resume
3. Handling of failed tickets while continuing execution
4. Listing of all resumable sprints with their status

**Expected Output:**
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                     Orchestrator Crash Recovery Demo                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Setting up test database...

================================================================================
  Demo 1: Basic Sprint Execution
================================================================================

Starting a sprint with 5 tickets...
[ORCHESTRATOR] Starting sprint: Demo Sprint 1 (ID: 101)
[ORCHESTRATOR] Fetching tickets for sprint 101
[ORCHESTRATOR] Ticket queue: ['SDT1-1', 'SDT1-2', 'SDT1-3', 'SDT1-4', 'SDT1-5']
[ORCHESTRATOR] Created state: <uuid>
[ORCHESTRATOR] Executing 5 tickets
[ORCHESTRATOR] Processing ticket: SDT1-1
[ORCHESTRATOR] Executing ticket: SDT1-1
[ORCHESTRATOR] ✓ Completed: SDT1-1
...
```

## Running Examples

### Prerequisites

1. Set up your Python environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r uat/backend/requirements.txt
```

2. Set environment variables:
```bash
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
# For demo purposes, SQLite in-memory database is used automatically
```

### Interactive Mode

You can also use the examples as a starting point for your own scripts:

```python
from examples.orchestrator_crash_recovery_demo import setup_test_database
from agents.orchestrator import Orchestrator

# Setup
db_session = setup_test_database()

# Create orchestrator
orch = Orchestrator("SDT1", db=db_session, verbose=True)

# Your code here...
```

## Creating Your Own Examples

Use the demo scripts as templates:

```python
#!/usr/bin/env python3
import sys
import os

# Add imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../uat/backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.orchestrator import Orchestrator
from agents.orchestrator_state import StateManager

def my_example():
    """Your example description."""
    # Your code here
    pass

if __name__ == "__main__":
    my_example()
```

## Testing Examples

Run the test suite to verify all examples work correctly:

```bash
# Run all orchestrator tests
pytest uat/backend/tests/test_orchestrator*.py -v

# Run specific test file
pytest uat/backend/tests/test_orchestrator_integration.py -v

# Run with coverage
pytest uat/backend/tests/test_orchestrator*.py --cov=agents --cov-report=html
```

## Troubleshooting

### Import Errors

If you get import errors, make sure you're running from the project root:
```bash
cd /path/to/project
python examples/orchestrator_crash_recovery_demo.py
```

### Database Errors

The demo uses an in-memory SQLite database by default, so no external database is required. If you want to use a real database:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# Use real database
engine = create_engine("postgresql://user:pass@localhost/dbname")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
db_session = SessionLocal()
```

## Additional Resources

- [Orchestrator State Persistence Documentation](../docs/orchestrator-state-persistence.md)
- [API Reference](../docs/api-reference.md)
- [CLI Tool Documentation](../agents/cli_orchestrator.py)

## Contributing

To add a new example:

1. Create a new Python file in this directory
2. Follow the template structure above
3. Add documentation to this README
4. Test thoroughly
5. Submit a PR

Example naming convention:
- `orchestrator_<feature>_example.py` - Feature demonstrations
- `orchestrator_<scenario>_demo.py` - Scenario walkthroughs
