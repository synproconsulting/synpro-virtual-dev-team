# Fix Version Tool Documentation

## Overview

The **CreateOrGetFixVersionTool** provides deterministic management of Jira fix versions (releases). This tool ensures that calling it multiple times with the same version name always returns the same version ID, making it safe to use in automated workflows without creating duplicates.

## Use Cases

Fix versions in Jira are used to:
- Track which release a feature or bug fix will be delivered in
- Group related issues for coordinated releases
- Plan and communicate release schedules to stakeholders
- Filter and report on work by release version

## Tools

### create_or_get_fix_version

**Description:** Get an existing fix version by name, or create it if it doesn't exist.

**Parameters:**
- `name` (required): Version name (e.g., 'v1.0.0', 'Sprint 1 Release', 'Q2 2025')
- `description` (optional): Human-readable description of the version
- `release_date` (optional): Target release date in ISO format (YYYY-MM-DD)
- `released` (optional): Boolean indicating if version is already released (default: False)

**Returns:**
- Version ID (deterministic - same name always returns same ID)
- Version name
- Whether it was newly created or existing

**Example Usage (CrewAI Agent):**
```python
result = create_or_get_fix_version(
    name="v2.1.0",
    description="Sprint 5 Release - User Authentication Features",
    release_date="2025-06-15",
    released=False
)
# Returns: "Created fix version: ID=10025 — v2.1.0"
# or: "Found existing fix version: ID=10025 — v2.1.0"
```

**Deterministic Behavior:**
```python
# First call creates the version
result1 = create_or_get_fix_version(name="v1.0.0")
# Returns: ID=10001, created=True

# Second call returns the same version
result2 = create_or_get_fix_version(name="v1.0.0")
# Returns: ID=10001, created=False

# Even with different parameters, same name returns same ID
result3 = create_or_get_fix_version(name="v1.0.0", description="Updated description")
# Returns: ID=10001, created=False (description update is ignored for existing versions)
```

### list_fix_versions

**Description:** List all fix versions (releases) for the project.

**Parameters:** None

**Returns:** Formatted list of all versions with ID, name, release status, and release date

**Example Usage:**
```python
result = list_fix_versions()
# Returns:
# Fix Versions:
#   • [10001] v1.0.0 — Released | Release: 2025-01-15
#   • [10002] v1.1.0 — Unreleased
#   • [10003] v2.0.0 — Unreleased | Release: 2025-06-30
```

## Integration with PM Agent

The PM Agent can use these tools to:

1. **Plan Releases:** Create fix versions for upcoming releases during sprint planning
2. **Track Progress:** Assign stories to specific versions to group related work
3. **Coordinate Deliverables:** Ensure all stories for a release are completed together
4. **Report Status:** Query which features are in which releases

**Example Workflow:**
```python
# 1. Agent creates a new release version
version_result = create_or_get_fix_version(
    name="Q2 2025 Release",
    description="All features for Q2 quarterly release",
    release_date="2025-06-30"
)

# 2. Agent can then assign stories to this version
# (This would be done through update_issue with fixVersions field)

# 3. Later, when checking on the release, the agent can list versions
versions = list_fix_versions()
```

## Implementation Details

### Backend Functions (jira_client.py)

#### `list_fix_versions() -> list[dict[str, Any]]`

Retrieves all fix versions for the project using the Jira REST API.

**Returns:** List of dictionaries with:
- `id`: Version ID (string)
- `name`: Version name
- `description`: Version description
- `released`: Boolean indicating release status
- `release_date`: Release date in YYYY-MM-DD format (if set)

#### `create_or_get_fix_version(name, description, release_date, released) -> dict[str, Any]`

Implements the deterministic create-or-get pattern:

1. Queries all existing versions
2. Searches for a version matching the provided name
3. If found, returns existing version ID with `created=False`
4. If not found, creates new version and returns ID with `created=True`

**Returns:** Dictionary with:
- `id`: Version ID (deterministic for same name)
- `name`: Version name
- `created`: Boolean indicating if version was newly created

### Error Handling

The tools handle common error scenarios:

- **Missing Environment Variables:** Raises `ValueError` if JIRA_URL, JIRA_EMAIL, or JIRA_API_TOKEN not set
- **Invalid Project:** Raises error if JIRA_PROJECT_KEY is invalid
- **API Connection Issues:** Underlying Jira library handles retries and connection errors
- **Duplicate Version Names:** Deterministic behavior prevents duplicates - always returns existing version

## Testing

Comprehensive test coverage includes:

- **Unit Tests** (`tests/test_fix_versions.py`):
  - Test deterministic behavior (same name → same ID)
  - Test version creation with all fields
  - Test version retrieval for existing versions
  - Test empty version lists
  - Test tool wrapper functionality
  - Test schema validation

**Run Tests:**
```bash
pytest tests/test_fix_versions.py -v
```

## Best Practices

1. **Consistent Naming:** Use a consistent naming convention for versions (e.g., semantic versioning: v1.0.0, v1.1.0)

2. **Descriptive Names:** Include release context in the name:
   - ✅ "Q2 2025 Release"
   - ✅ "Sprint 10 Delivery"
   - ✅ "v2.1.0 - Authentication Feature"
   - ❌ "Release 1"
   - ❌ "Next version"

3. **Use Descriptions:** Provide context in the description field about what's included

4. **Set Release Dates:** Always include target release dates for planning purposes

5. **Don't Modify Existing Versions:** The tool returns existing versions as-is. If you need to update a version, use the Jira UI or direct API calls

6. **Check Before Creating:** Use `list_fix_versions()` first to see what versions exist if you're unsure

## Limitations

- **No Update Capability:** The tool doesn't update existing versions. If you call it with the same name but different parameters, it returns the existing version unchanged.

- **No Deletion:** The tool doesn't delete versions. Use Jira UI for version cleanup.

- **Project Scope:** Versions are project-scoped. Each project has its own independent set of versions.

## Related Documentation

- [Jira Fix Versions Official Docs](https://support.atlassian.com/jira-software-cloud/docs/manage-versions/)
- [PM Agent Architecture](../agents/pm_agent.py)
- [Jira Client API](../tools/jira_client.py)
