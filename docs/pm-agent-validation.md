# PM Agent Validation

## Overview

The PM Agent validation system ensures that all Jira stories created by the PM Agent meet quality standards and contain the required fields for proper execution by the Orchestrator.

## Critical Requirement: execution_order

**Every story MUST have `execution_order` set.**

The `execution_order` field (Jira custom field `customfield_10071`) is critical for the Orchestrator to:
- Sequence tickets in the correct dependency order
- Execute stories in the proper sequence
- Prevent dependency conflicts during sprint execution

**Stories without `execution_order` cannot be executed by the Orchestrator and will block the sprint.**

## Validation Tools

The PM Agent has access to two validation tools:

### 1. `validate_story`

Validates a story's parameters **before** creation.

**Usage:**
```python
validate_story(
    summary="Implement user login",
    description="As a user, I want to...",
    epic_key="SDT1-1",
    story_points=3,
    priority="High",
    execution_order=1
)
```

**Checks:**
- ❌ **CRITICAL**: Missing `execution_order` (ERROR)
- ❌ **CRITICAL**: Invalid `execution_order` (< 1) (ERROR)
- ⚠️ Missing epic link (WARNING)
- ⚠️ Missing story points (WARNING)
- ⚠️ Story points > 8 (WARNING - consider splitting)
- ⚠️ Summary > 100 characters (WARNING)
- ⚠️ Description too short (< 20 chars) (WARNING)

**Returns:**
- `✅ Validation passed` - No issues found
- `⚠️ VALIDATION WARNINGS` - Non-critical issues found
- `❌ VALIDATION FAILED` - Critical errors found

### 2. `validate_backlog`

Audits the entire backlog for quality issues.

**Usage:**
```python
validate_backlog()
```

**Output Example:**
```
📋 Backlog Validation Report
==================================================

Total Stories: 15

❌ CRITICAL: 3 stories missing execution_order
   → These stories CANNOT be executed by the Orchestrator!
   → Affected tickets: SDT1-42, SDT1-43, SDT1-44

⚠️  5 stories not linked to an Epic
⚠️  2 stories missing story points
⚠️  1 stories with > 8 story points (consider splitting)
ℹ️  3 stories with short/missing descriptions

❌ Backlog has CRITICAL issues that must be fixed before sprint planning!
```

## Validation Severity Levels

### ERROR (❌)
**Critical issues that must be fixed immediately.**

- Missing `execution_order` - Story cannot be executed
- Invalid `execution_order` (< 1) - Invalid value

Stories with ERROR-level issues will block sprint execution.

### WARNING (⚠️)
**Best practice violations that should be addressed.**

- Missing epic link - Affects organization and tracking
- Missing story points - Affects sprint planning capacity
- Story points > 8 - Story may be too complex
- Long summary (> 100 chars) - Readability concern

Warnings should be addressed to maintain backlog quality, but won't block execution.

### INFO (ℹ️)
**Minor issues for improvement.**

- Short/missing description - May lack context
- Other quality concerns

## Best Practices

### 1. Always Validate Before Creating

```python
# ✅ Good: Validate first
validate_story(
    summary="Add user profile page",
    description="...",
    epic_key="SDT1-1",
    story_points=3,
    execution_order=5
)

create_story(
    summary="Add user profile page",
    description="...",
    epic_key="SDT1-1",
    story_points=3,
    execution_order=5
)
```

```python
# ❌ Bad: Create without validation
create_story(
    summary="Add user profile page",
    description="...",
    execution_order=None  # Will fail later!
)
```

### 2. Audit Backlog Before Sprint Planning

```python
# Run before starting a new sprint
validate_backlog()

# Fix any critical issues
# Then proceed with sprint planning
```

### 3. Set execution_order Based on Dependencies

```python
# Story 1: Foundation work (no dependencies)
create_story(
    summary="Set up database schema",
    execution_order=1,  # Executed first
    ...
)

# Story 2: Depends on Story 1
create_story(
    summary="Implement data access layer",
    execution_order=2,  # Executed after Story 1
    ...
)

# Story 3: Independent work
create_story(
    summary="Design UI mockups",
    execution_order=3,  # Can run in parallel with Story 2
    ...
)
```

### 4. Use Issue Links to Document Dependencies

```python
# Create blocker relationship
create_blocker_link(
    blocker_issue_key="SDT1-1",  # This must be done first
    blocked_issue_key="SDT1-2"    # This is blocked by SDT1-1
)

# execution_order should reflect this:
# SDT1-1: execution_order=1
# SDT1-2: execution_order=2
```

## Integration with Orchestrator

The Orchestrator uses `execution_order` to sequence ticket execution:

1. **Fetch Sprint Tickets**: Get all stories in the sprint
2. **Sort by execution_order**: Stories sorted ascending (1, 2, 3, ...)
3. **Execute in Sequence**: Process each ticket in order
4. **Handle Failures**: Log and continue to next ticket

Without `execution_order`, the Orchestrator cannot determine the correct execution sequence, leading to:
- Dependency conflicts
- Failed ticket execution
- Blocked sprints

## API Reference

### PMValidator Class

```python
from tools.pm_validation import PMValidator

validator = PMValidator()

# Validate story creation
valid = validator.validate_story_creation(
    summary="...",
    description="...",
    epic_key="...",
    story_points=3,
    execution_order=1
)

# Validate backlog
results = validator.validate_backlog_health(issues)

# Get warnings
warnings = validator.get_warnings()

# Check for errors
has_errors = validator.has_errors()

# Format warnings
output = validator.format_warnings()

# Clear warnings
validator.clear_warnings()
```

### Convenience Functions

```python
from tools.pm_validation import validate_story_creation, get_validator

# Quick validation
result = validate_story_creation(
    summary="...",
    execution_order=1,
    ...
)

# Get global validator
validator = get_validator()
```

## Testing

Run tests with pytest:

```bash
pytest tools/test_pm_validation.py -v
```

Tests cover:
- Validation logic for all check types
- Error and warning detection
- Backlog health auditing
- Edge cases (empty descriptions, invalid values, etc.)

## Migration Guide

If you have existing stories without `execution_order`:

1. **Identify affected stories:**
   ```python
   validate_backlog()
   ```

2. **Analyze dependencies:**
   ```python
   list_issue_links(issue_key="SDT1-42")
   ```

3. **Set execution_order:**
   ```python
   # Use update_issue to add execution_order
   # Note: This requires updating jira_client.update_issue to support execution_order
   ```

4. **Verify:**
   ```python
   validate_backlog()
   ```

## Troubleshooting

### "Missing execution_order" Error

**Problem:** Story created without `execution_order`

**Solution:**
1. Determine the correct execution sequence
2. Consider dependencies (use `list_issue_links`)
3. Set `execution_order` when creating the story
4. Or update existing story with correct value

### "Cannot execute story" in Orchestrator

**Problem:** Orchestrator skips or fails on story

**Solution:**
1. Check if story has `execution_order` set
2. Run `validate_backlog()` to find missing values
3. Update story with correct `execution_order`
4. Resume sprint execution

### Validation Warnings on Good Stories

**Problem:** Valid stories showing warnings

**Solution:**
- Review warning message for specific issue
- Warnings are recommendations, not blockers
- Address warnings to improve backlog quality
- Critical: Only ERROR-level issues block execution

## Future Enhancements

Potential improvements to validation:

1. **Dependency Cycle Detection**: Warn about circular dependencies
2. **Execution Order Gaps**: Detect gaps in execution sequence
3. **Sprint Capacity Validation**: Warn when sprint exceeds team velocity
4. **Custom Validation Rules**: Allow project-specific validation rules
5. **Automated Fixes**: Suggest or auto-apply fixes for common issues

## References

- [PM Agent Documentation](../agents/pm_agent.py)
- [Orchestrator Documentation](../agents/orchestrator.py)
- [Jira Custom Fields](../tools/jira_client.py)
