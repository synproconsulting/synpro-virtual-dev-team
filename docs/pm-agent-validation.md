# PM Agent Validation

## Overview

The PM Agent now includes built-in validation to ensure data quality when creating Jira stories. This validation helps prevent common issues that could block the Orchestrator and downstream automation.

## Validation Rules

### Critical: execution_order

**Rule**: Every story MUST have an `execution_order` value set.

**Why**: The Orchestrator uses `execution_order` (stored in `customfield_10071`) to sequence ticket execution. Stories without this field will not be picked up by the automated workflow, blocking sprint progress.

**Severity**: ⚠️ WARNING

**Example Warning**:
```
⚠️  WARNING: execution_order not set (SDT1-123). 
This story will not be sequenced correctly by the Orchestrator. 
Set execution_order based on dependencies: blockers get lower numbers, 
blocked stories get higher numbers.
```

### Informational: Epic Linkage

**Rule**: Stories should be linked to an Epic for better organization.

**Why**: Grouping related stories under Epics improves backlog organization and makes it easier to track feature progress.

**Severity**: ℹ️ INFO

**Example Info**:
```
ℹ️  INFO: Story not linked to an Epic. 
Consider grouping related stories under an Epic for better organization.
```

### Informational: Summary Length

**Rule**: Story summaries should be under 100 characters.

**Why**: Long summaries are harder to read in Jira list views and boards.

**Severity**: ℹ️ INFO

**Example Info**:
```
ℹ️  INFO: Summary is 120 characters (recommended: <100). 
Consider shortening for better readability in Jira views.
```

## How It Works

### CreateStoryTool

When the PM Agent calls `create_story`, validation runs automatically before the story is created:

```python
tool = CreateStoryTool()
result = tool._run(
    summary="Implement user authentication",
    description="As a user, I want to...",
    epic_key="SDT1-1",
    story_points=5,
    priority="High",
    execution_order=None,  # ⚠️  Missing!
)
```

**Response**:
```
Story created: SDT1-42 — Implement user authentication

⚠️  WARNING: execution_order not set. 
This story will not be sequenced correctly by the Orchestrator. 
Set execution_order based on dependencies: blockers get lower numbers, 
blocked stories get higher numbers.
```

The story is still created in Jira, but the warning is returned to the agent so it can take corrective action.

## Best Practices

### Setting execution_order

1. **Analyze dependencies first**: Use `list_issue_links` to understand existing dependencies
2. **Blockers get low numbers**: Stories that others depend on should have execution_order 1, 2, 3, etc.
3. **Blocked stories get high numbers**: Stories that can't start until others are done get higher numbers
4. **Sequential within epics**: Related stories in the same epic should have sequential numbers

**Example**:
```
Epic: User Management (SDT1-1)
├── Story: Database schema (SDT1-10) → execution_order: 1
├── Story: API endpoints (SDT1-11) → execution_order: 2
└── Story: UI components (SDT1-12) → execution_order: 3
```

### When to Override Validation

Validation warnings are informational — they don't prevent story creation. Override them when:

- **Rapid prototyping**: During initial backlog grooming, you may want to create stories quickly and add execution_order later
- **Non-development stories**: Administrative stories (e.g., "Schedule team meeting") may not need execution_order
- **Backlog refinement**: Stories being prepared for future sprints may not need execution_order until sprint planning

However, **before adding stories to an active sprint**, always ensure execution_order is set.

## Testing

Validation is covered by comprehensive unit and integration tests:

```bash
# Run validation unit tests
pytest tools/tests/test_validation.py

# Run integration tests
pytest tools/tests/test_pm_tools_validation.py
```

## Implementation Details

### Architecture

- **Validation Module**: `tools/validation.py` — Core validation logic
- **Integration**: `tools/pm_tools.py` — CreateStoryTool calls validation before creating stories
- **Tests**: `tools/tests/test_validation.py` and `tools/tests/test_pm_tools_validation.py`

### Custom Fields

- `customfield_10071` — execution_order (integer)
- `customfield_10016` — story_points (integer)

### Extending Validation

To add new validation rules:

1. Add the validation function to `tools/validation.py`:
   ```python
   def validate_new_field(field_value: Any) -> str:
       """Validate a new field."""
       if not is_valid(field_value):
           return "⚠️  WARNING: Invalid value..."
       return ""
   ```

2. Update `validate_story_creation` to include the new check:
   ```python
   def validate_story_creation(...) -> list[str]:
       warnings = []
       
       # Existing validations...
       
       # New validation
       new_warning = validate_new_field(new_field)
       if new_warning:
           warnings.append(new_warning)
       
       return warnings
   ```

3. Add tests to `tools/tests/test_validation.py`

## Related Documentation

- [PM Agent Documentation](../agents/pm_agent.py) — PM Agent responsibilities and backstory
- [Orchestrator Documentation](../docs/orchestrator.md) — How execution_order drives ticket sequencing
- [Jira Custom Fields](../docs/jira-custom-fields.md) — Complete list of custom fields

## Troubleshooting

### "Stories not being picked up by Orchestrator"

**Symptom**: Stories in sprint but not getting executed

**Solution**: Check execution_order field:
```python
from tools import jira_client
issues = jira_client.list_all_issues()
for issue in issues:
    print(jira_client.format_issue(issue))
```

Look for stories showing `Order: None` and update them:
```python
from tools import jira_client
jira_client.update_issue("SDT1-123", story_points=5)
# Note: update_issue doesn't currently support execution_order,
# use Jira UI or add the parameter to the function
```

### "Too many validation warnings"

**Symptom**: Agent responses are cluttered with warnings

**Solution**: 
1. Improve PM Agent prompts to always set execution_order
2. Filter informational (ℹ️ INFO) messages if they're not actionable
3. Adjust validation thresholds (e.g., change summary length limit from 100 to 120 characters)

## Changelog

### v1.0.0 (SDT1-65)
- Initial implementation of execution_order validation
- Added informational validation for epic linkage and summary length
- Comprehensive test coverage for validation logic
- Integration with CreateStoryTool
