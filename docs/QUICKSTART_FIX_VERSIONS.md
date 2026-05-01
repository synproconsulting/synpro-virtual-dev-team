# Quick Start: Fix Version Management

## 1-Minute Setup

### Prerequisites
Ensure your `.env` file has:
```bash
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=YOUR-PROJECT
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Basic Usage

### In Python Code

```python
from tools import jira_client

# Create or get a version (deterministic)
result = jira_client.create_or_get_fix_version(
    name="v1.0.0",
    description="Initial release",
    release_date="2025-07-01"
)
print(f"Version ID: {result['id']}")

# List all versions
versions = jira_client.list_fix_versions()
for v in versions:
    print(f"{v['name']}: {v['id']}")
```

### In PM Agent (CrewAI)

The PM Agent has access to these tools:

```python
# Agent can use these tools naturally in conversation:
create_or_get_fix_version(
    name="Sprint 5 Release",
    description="All features from Sprint 5",
    release_date="2025-06-15"
)

list_fix_versions()
```

## Common Patterns

### Pattern 1: Sprint-Based Releases
```python
# Create a version for each sprint
for sprint_num in range(1, 6):
    jira_client.create_or_get_fix_version(
        name=f"Sprint {sprint_num} Delivery",
        release_date=f"2025-0{sprint_num}-15"
    )
```

### Pattern 2: Semantic Versioning
```python
# Major, minor, patch releases
versions = ["v2.0.0", "v2.1.0", "v2.1.1", "v2.2.0"]
for version in versions:
    jira_client.create_or_get_fix_version(name=version)
```

### Pattern 3: Quarterly Releases
```python
quarters = [
    ("Q1 2025", "2025-03-31"),
    ("Q2 2025", "2025-06-30"),
    ("Q3 2025", "2025-09-30"),
    ("Q4 2025", "2025-12-31"),
]
for name, date in quarters:
    jira_client.create_or_get_fix_version(name=name, release_date=date)
```

## Key Concepts

### Deterministic Behavior
✅ **Safe to call multiple times**
```python
# First call creates
result1 = create_or_get_fix_version(name="v1.0.0")  # created=True

# Second call returns existing
result2 = create_or_get_fix_version(name="v1.0.0")  # created=False

# Same ID every time
assert result1['id'] == result2['id']  # ✓ True
```

### Version Scope
- Versions are **project-specific**
- Each project has independent versions
- Version names must be unique within a project

## Testing

### Run Unit Tests
```bash
# All unit tests (fast)
pytest tests/test_fix_versions.py

# With coverage
pytest tests/test_fix_versions.py --cov=tools
```

### Run Integration Tests
```bash
# Requires live Jira connection
pytest tests/integration/test_fix_version_integration.py -v -m integration

# Skip integration tests (default)
pytest -m "not integration"
```

## Troubleshooting

### Error: Missing environment variables
**Solution:** Ensure `.env` has `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY`

### Error: Version already exists with different details
**Expected:** Tool returns existing version unchanged. This is intentional (deterministic behavior).
**Solution:** If you need to update a version, do it manually in Jira UI.

### Error: Connection timeout
**Solution:** Check your network connection and Jira API token validity.

## Examples

See `examples/fix_version_example.py` for comprehensive examples:
```bash
python examples/fix_version_example.py
```

## Next Steps

- Read full documentation: [`docs/fix_version_tool.md`](./fix_version_tool.md)
- Explore PM Agent integration: [`agents/pm_agent.py`](../agents/pm_agent.py)
- Review API reference: [`tools/jira_client.py`](../tools/jira_client.py)
