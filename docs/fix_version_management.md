# Fix Version Management

## Overview

The PM Agent now includes deterministic fix version management tools that allow for idempotent creation and retrieval of Jira fix versions (releases). This enables reliable release planning and ensures that multiple calls with the same version name always return the same version ID.

## Features

### 1. Deterministic Version IDs

The `create_or_get_fix_version` function ensures that:
- Calling it with the same version name always returns the same version ID
- No duplicate versions are created
- The operation is idempotent and safe to call multiple times

### 2. Complete Version Lifecycle Support

Manage versions through their entire lifecycle:
- **Unreleased**: Default state for new versions
- **Released**: Mark versions as released when deployed
- **Archived**: Archive old versions to keep the list clean

### 3. Integration with PM Agent

The PM Agent can now:
- Create fix versions for sprints and releases
- Tag issues with fix versions for release tracking
- List existing versions before creating new ones
- Ensure consistent version naming across the project

## Usage

### Creating or Getting a Fix Version

```python
from tools import jira_client

# Create a new version or get existing one
result = jira_client.create_or_get_fix_version(
    name="Sprint 1 - Q1 2025",
    description="First sprint of Q1",
    release_date="2025-02-01",
    archived=False,
    released=False
)

print(f"Version ID: {result['id']}")
print(f"Created: {result['created']}")  # True if new, False if existing
```

### Listing Fix Versions

```python
from tools import jira_client

# List all unreleased versions
versions = jira_client.list_fix_versions(
    include_archived=False,
    include_released=False
)

for version in versions:
    print(f"{version['name']} (ID: {version['id']})")
```

## PM Agent Tool Usage

### create_or_get_fix_version

Creates a new fix version or retrieves an existing one by name.

**Parameters:**
- `name` (required): The version name (must be unique within project)
- `description` (optional): Description of the version/release
- `release_date` (optional): Release date in YYYY-MM-DD format
- `archived` (optional): Whether the version is archived (default: False)
- `released` (optional): Whether the version has been released (default: False)

**Returns:**
A deterministic version ID that can be used to tag issues.

**Example Agent Call:**
```
I need to create a fix version for Sprint 1.

Tool: create_or_get_fix_version
Parameters:
  name: "Sprint 1 - Authentication"
  description: "User authentication and authorization features"
  release_date: "2025-02-15"
```

**Output:**
```
Fix version created: Sprint 1 - Authentication (ID: 12345)
  Description: User authentication and authorization features
  Release date: 2025-02-15
  Status: Unreleased
```

### list_fix_versions

Lists all fix versions in the project with optional filtering.

**Parameters:**
- `include_archived` (optional): Include archived versions (default: False)
- `include_released` (optional): Include released versions (default: True)

**Example Agent Call:**
```
Show me all active fix versions.

Tool: list_fix_versions
Parameters:
  include_archived: false
  include_released: false
```

**Output:**
```
Fix versions:
  [12345] Sprint 1 - Authentication — Unreleased | Release: 2025-02-15
  [12346] Sprint 2 - Dashboard — Unreleased | Release: 2025-03-01
```

## Best Practices

### 1. Consistent Naming

Use a consistent naming convention for versions:
- **Sprint-based**: "Sprint 1 - Q1 2025", "Sprint 2 - Q1 2025"
- **Semantic versioning**: "v1.0.0", "v1.1.0", "v2.0.0"
- **Date-based**: "Release 2025-Q1", "Release 2025-Q2"

### 2. Check Before Creating

Always list existing versions before creating new ones to avoid naming conflicts:

```python
# List existing versions
existing = jira_client.list_fix_versions()

# Check if version name is already in use
version_names = [v['name'] for v in existing]
if "Sprint 1" not in version_names:
    result = jira_client.create_or_get_fix_version(name="Sprint 1")
```

### 3. Set Release Dates

Always provide a target release date to help with planning:

```python
result = jira_client.create_or_get_fix_version(
    name="Sprint 3",
    release_date="2025-03-15"
)
```

### 4. Use Descriptions

Add meaningful descriptions to help team members understand the release scope:

```python
result = jira_client.create_or_get_fix_version(
    name="v1.0.0",
    description="Initial public release with core features: authentication, dashboard, and reporting"
)
```

## Integration with Sprint Planning

Fix versions work seamlessly with sprint planning:

1. **Create Sprint and Fix Version**:
   ```python
   # Create sprint
   sprint = jira_client.create_sprint(
       name="Sprint 1",
       goal="Implement authentication"
   )
   
   # Create matching fix version
   version = jira_client.create_or_get_fix_version(
       name="Sprint 1 - Authentication",
       release_date="2025-02-15"
   )
   ```

2. **Tag Issues**: After creating stories, tag them with the fix version ID to track which release they belong to.

3. **Release Management**: When the sprint completes, mark the fix version as released.

## Technical Details

### Idempotency

The `create_or_get_fix_version` function implements idempotency by:

1. Querying all existing versions in the project
2. Checking if a version with the requested name exists
3. If exists: returning the existing version (created=False)
4. If not: creating a new version (created=True)

This ensures that:
- Multiple calls with the same name return the same ID
- No duplicate versions are created
- The operation is safe to retry

### Version ID Format

Jira fix version IDs are numeric strings (e.g., "12345"). The ID is:
- Automatically assigned by Jira
- Guaranteed unique within the Jira instance
- Deterministic for a given version name
- Persistent across API calls

### Error Handling

The functions handle common error cases:

- **Missing environment variables**: Raises `ValueError` with clear message
- **Invalid project key**: Jira API returns error
- **Network issues**: Jira client retries with exponential backoff
- **Invalid dates**: Jira API validates date format

## Testing

The implementation includes comprehensive unit tests:

- ✅ Creating new versions
- ✅ Retrieving existing versions
- ✅ Idempotent behavior across multiple calls
- ✅ Filtering by archived/released status
- ✅ Handling empty project
- ✅ Multiple versions with correct selection
- ✅ Tool wrapper integration

Run tests:
```bash
pytest tools/tests/test_fix_version.py -v
```

## Environment Variables

No additional environment variables required. Uses existing Jira configuration:

- `JIRA_URL`: Jira instance URL
- `JIRA_EMAIL`: Jira user email
- `JIRA_API_TOKEN`: Jira API token
- `JIRA_PROJECT_KEY`: Project key (e.g., "SDT1")

## API Reference

### jira_client.create_or_get_fix_version

```python
def create_or_get_fix_version(
    name: str,
    description: str = "",
    release_date: Optional[str] = None,
    archived: bool = False,
    released: bool = False,
) -> dict[str, Any]:
    """
    Create or retrieve a fix version with deterministic ID.
    
    Returns:
        {
            "id": str,              # Version ID
            "name": str,            # Version name
            "description": str,     # Version description
            "archived": bool,       # Archived status
            "released": bool,       # Released status
            "release_date": str,    # Release date (YYYY-MM-DD)
            "created": bool         # True if newly created
        }
    """
```

### jira_client.list_fix_versions

```python
def list_fix_versions(
    include_archived: bool = False,
    include_released: bool = True,
) -> list[dict[str, Any]]:
    """
    List all fix versions in the project.
    
    Returns:
        List of version dictionaries with id, name, description,
        archived, released, and release_date fields.
    """
```

## Examples

### Example 1: Sprint Planning Workflow

```python
# 1. List existing versions to avoid conflicts
versions = jira_client.list_fix_versions(include_released=False)
print(f"Active versions: {len(versions)}")

# 2. Create version for new sprint
version = jira_client.create_or_get_fix_version(
    name="Sprint 5 - Q1 2025",
    description="Mobile app enhancements",
    release_date="2025-02-28"
)
print(f"Version ID: {version['id']}")

# 3. Create sprint
sprint = jira_client.create_sprint(
    name="Sprint 5",
    goal="Mobile app enhancements"
)

# 4. Create and tag stories (version ID would be used here)
```

### Example 2: Release Management

```python
# List unreleased versions
unreleased = jira_client.list_fix_versions(
    include_released=False,
    include_archived=False
)

for version in unreleased:
    print(f"Pending: {version['name']} → {version['release_date']}")
```

### Example 3: Version Lifecycle

```python
# Create new version
v1 = jira_client.create_or_get_fix_version(
    name="v1.0.0",
    description="Initial release"
)

# Later: Mark as released (would use Jira update API)
# jira.update_version(v1['id'], released=True)

# Even later: Archive old version
# jira.update_version(v1['id'], archived=True)
```

## Troubleshooting

### Issue: "No fix versions found"

**Cause**: Project has no versions or all are filtered out.

**Solution**: 
- Check if project has any versions in Jira UI
- Adjust `include_archived` and `include_released` parameters

### Issue: Version created but ID changes

**Cause**: This shouldn't happen with the deterministic implementation.

**Solution**: 
- Verify you're using the same version name exactly
- Check for trailing spaces or case differences
- Use `list_fix_versions()` to see all versions

### Issue: Cannot create version

**Cause**: Permission issues or invalid project key.

**Solution**:
- Verify `JIRA_PROJECT_KEY` environment variable
- Ensure Jira user has "Administer Projects" permission
- Check Jira API token is valid

## Future Enhancements

Potential future improvements:

1. **Auto-versioning**: Automatically increment version numbers
2. **Version templates**: Predefined templates for common version patterns
3. **Bulk operations**: Create multiple versions at once
4. **Version analytics**: Track issue completion across versions
5. **Version dependencies**: Link versions to show release dependencies
