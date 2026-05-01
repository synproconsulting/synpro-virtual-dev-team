# PM Agent Tools

This directory contains the CrewAI-compatible tools that the PM Agent uses to interact with Jira.

## Structure

- **`jira_client.py`**: Low-level Jira REST API client with project-specific defaults
- **`pm_tools.py`**: CrewAI tool wrappers that the PM Agent can call by name
- **`tests/`**: Unit tests for tools and Jira client functions

## Available Tools

### Backlog Management

1. **`list_backlog`**: List all issues in the backlog (not in any sprint)
2. **`list_all_issues`**: List all open issues regardless of sprint
3. **`create_epic`**: Create a new Epic in Jira
4. **`create_story`**: Create a new Story, optionally linked to an Epic
5. **`update_issue`**: Update issue fields (summary, description, priority, story points)

### Sprint Management

6. **`list_sprints`**: List all active and future sprints
7. **`create_sprint`**: Create a new sprint on the project board
8. **`add_issues_to_sprint`**: Move backlog issues into a sprint
9. **`transition_issue`**: Move an issue to a new workflow status
10. **`add_comment`**: Post a comment on a Jira issue

### Dependency Management

11. **`create_blocker_link`**: Create a "blocks" relationship between issues
12. **`list_issue_links`**: List all links for an issue

### Fix Version Management (NEW in SDT1-57)

13. **`create_or_get_fix_version`**: Create or retrieve a fix version with deterministic ID
14. **`list_fix_versions`**: List all fix versions in the project

## Fix Version Tools

### create_or_get_fix_version

Creates a new fix version (release) or retrieves an existing one with the same name. This tool is **idempotent** - calling it multiple times with the same name will return the same fix version ID.

**Use Cases:**
- Sprint planning: Create a fix version for each sprint
- Release management: Track which features go into which releases
- Version tagging: Get deterministic IDs to tag issues

**Parameters:**
- `name` (required): Version name (unique within project)
- `description` (optional): Description of the version/release
- `release_date` (optional): Target release date (YYYY-MM-DD format)
- `archived` (optional): Whether the version is archived (default: False)
- `released` (optional): Whether the version has been released (default: False)

**Returns:**
- Version ID (deterministic for the same name)
- Whether the version was newly created or already existed
- All version metadata

**Example:**
```python
from tools.pm_tools import CreateOrGetFixVersionTool

tool = CreateOrGetFixVersionTool()
result = tool._run(
    name="Sprint 1 - Authentication",
    description="User authentication and authorization features",
    release_date="2025-02-15"
)
# Output: Fix version created: Sprint 1 - Authentication (ID: 12345)
```

### list_fix_versions

Lists all fix versions in the project with optional filtering.

**Parameters:**
- `include_archived` (optional): Include archived versions (default: False)
- `include_released` (optional): Include released versions (default: True)

**Returns:**
List of all matching fix versions with their IDs, names, descriptions, and status.

**Example:**
```python
from tools.pm_tools import ListFixVersionsTool

tool = ListFixVersionsTool()
result = tool._run(include_archived=False, include_released=False)
# Output: Lists all unreleased, non-archived versions
```

## Custom Fields

The PM Agent uses the following Jira custom fields:

- **`customfield_10016`**: Story points (integer)
- **`customfield_10071`**: Execution order (integer) — used for dependency sequencing
- **`customfield_10014`**: Epic link (older Jira instances)
- **`parent`**: Epic link (newer Jira instances)

## Environment Variables

All tools require these environment variables:

```bash
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=SDT1
JIRA_BOARD_ID=1
```

## Tool Groups

Tools are organized into groups to stay within Claude's function schema limits:

### BACKLOG_TOOLS
- List backlog/issues
- Create epics/stories
- Update issues
- Manage blockers and links
- Manage fix versions (NEW)

### SPRINT_TOOLS
- List/create sprints
- Add issues to sprints
- Transition issues
- Add comments

### ALL_PM_TOOLS
Combined list of all tools for comprehensive PM Agent capabilities.

## Testing

Run the test suite:

```bash
# Run all tool tests
pytest tools/tests/ -v

# Run specific test file
pytest tools/tests/test_fix_version.py -v

# Run with coverage
pytest tools/tests/ --cov=tools --cov-report=html
```

## Adding New Tools

To add a new tool:

1. **Add the low-level function to `jira_client.py`**:
   ```python
   def my_new_function(param: str) -> dict[str, Any]:
       """Docstring explaining the function."""
       jira = _get_client()
       # Implementation
       return result
   ```

2. **Create input schema in `pm_tools.py`**:
   ```python
   class MyNewInput(BaseModel):
       param: str = Field(..., description="Parameter description")
   ```

3. **Create tool class in `pm_tools.py`**:
   ```python
   class MyNewTool(BaseTool):
       name: str = "my_new_tool"
       description: str = "What this tool does"
       args_schema: type = MyNewInput
       
       def _run(self, param: str) -> str:
           result = jira.my_new_function(param)
           return f"Operation completed: {result}"
   ```

4. **Add to appropriate tool group**:
   ```python
   BACKLOG_TOOLS = [
       # ... existing tools
       MyNewTool(),
   ]
   ```

5. **Write tests in `tools/tests/test_my_feature.py`**:
   ```python
   import pytest
   from unittest.mock import patch
   from tools import jira_client
   
   @patch('tools.jira_client._get_client')
   def test_my_new_function(mock_get_client):
       # Test implementation
       pass
   ```

## Best Practices

### 1. Idempotency
Make operations idempotent where possible (like `create_or_get_fix_version`). This allows safe retries and prevents duplicate data.

### 2. Deterministic IDs
When creating resources, check if they exist first and return the existing ID. This ensures consistent behavior across multiple calls.

### 3. Clear Error Messages
Raise `ValueError` with clear messages when environment variables are missing or parameters are invalid.

### 4. Type Hints
Use type hints on all functions and parameters for better IDE support and documentation.

### 5. Comprehensive Tests
Mock Jira API calls in tests to avoid dependencies on live Jira instances. Test happy paths, edge cases, and error conditions.

## Architecture

```
tools/
├── jira_client.py          # Low-level Jira API wrapper
├── pm_tools.py             # CrewAI tool wrappers
├── tests/
│   ├── __init__.py
│   └── test_fix_version.py # Unit tests
└── README.md               # This file

agents/
└── pm_agent.py             # PM Agent using these tools

docs/
└── fix_version_management.md  # Detailed documentation
```

## References

- [CrewAI Documentation](https://docs.crewai.com/)
- [Jira REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Jira Python Library](https://jira.readthedocs.io/)

## Recent Changes

### SDT1-57: PM Agent - CreateOrGetFixVersionTool with deterministic fix version ID

**Added:**
- `create_or_get_fix_version()` function in `jira_client.py`
- `list_fix_versions()` function in `jira_client.py`
- `CreateOrGetFixVersionTool` CrewAI tool wrapper
- `ListFixVersionsTool` CrewAI tool wrapper
- Comprehensive unit tests in `test_fix_version.py`
- Documentation in `docs/fix_version_management.md`

**Benefits:**
- Deterministic fix version IDs for consistent release tracking
- Idempotent operations prevent duplicate versions
- Integration with sprint planning workflow
- Full lifecycle support (unreleased → released → archived)

See `docs/fix_version_management.md` for detailed usage examples and best practices.
