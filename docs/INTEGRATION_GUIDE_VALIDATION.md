# PM Agent Validation - Integration Guide

## Quick Start

The PM Agent validation system helps catch issues before they block sprint execution.

### For PM Agent (AI)

You now have two new tools:

1. **`validate_story`** - Check a story before creating it
2. **`validate_backlog`** - Audit entire backlog health

#### Example: Creating a Story

```python
# STEP 1: Validate BEFORE creating
validate_story(
    summary="Add user dashboard",
    description="As a user, I want a dashboard...",
    epic_key="SDT1-1",
    story_points=5,
    execution_order=3  # ← REQUIRED!
)

# STEP 2: If validation passes, create the story
create_story(
    summary="Add user dashboard",
    description="As a user, I want a dashboard...",
    epic_key="SDT1-1",
    story_points=5,
    execution_order=3
)
```

#### Example: Auditing Backlog

```python
# Check backlog health before sprint planning
validate_backlog()

# Output shows:
# - Stories missing execution_order (CRITICAL)
# - Stories missing epic links
# - Stories missing estimates
# - Over-estimated stories (> 8 points)
```

### For Developers (Human)

#### Running Tests

```bash
# Run validation tests
pytest tools/test_pm_validation.py -v

# Run with coverage
pytest tools/test_pm_validation.py --cov=tools.pm_validation --cov-report=html

# Run all tests
pytest -v
```

#### Using Validation Programmatically

```python
from tools.pm_validation import validate_story_creation, get_validator

# Quick validation
result = validate_story_creation(
    summary="My story",
    description="Story description...",
    execution_order=1
)

print(result)
# Output: "✅ Validation passed" or "❌ VALIDATION FAILED"

# Advanced usage with validator object
validator = get_validator()
validator.clear_warnings()

is_valid = validator.validate_story_creation(
    summary="My story",
    execution_order=1,
    ...
)

if validator.has_errors():
    print("Critical errors found!")
    for warning in validator.get_warnings():
        if warning.severity == "ERROR":
            print(f"  - {warning.message}")
```

#### Integration with Existing Code

The validation system integrates seamlessly:

```python
from tools.pm_tools import CreateStoryTool

# Tool now includes automatic validation
tool = CreateStoryTool()

# Validation warnings appear in output automatically
result = tool._run(
    summary="Test story",
    description="Description...",
    execution_order=None  # ← This will trigger warning
)

print(result)
# Output includes:
# "Story created: SDT1-42 — Test story
#  
#  ❌ VALIDATION FAILED
#  
#  Validation Warnings:
#    [ERROR] Missing execution_order! ..."
```

## Validation Rules

### Critical Errors (❌)

These **must** be fixed:

- **Missing execution_order**: Story cannot be executed by Orchestrator
- **Invalid execution_order** (< 1): Invalid value

### Warnings (⚠️)

Best practices to follow:

- Missing epic link
- Missing story points
- Story points > 8 (consider splitting)
- Summary > 100 characters
- Short/missing description (< 20 chars)

## Common Scenarios

### Scenario 1: Creating Stories for a Sprint

```python
# 1. Validate backlog first
validate_backlog()

# 2. Fix any critical issues found

# 3. Create stories with proper execution_order
create_story(
    summary="Set up database",
    execution_order=1,  # First
    ...
)

create_story(
    summary="Implement API endpoints",
    execution_order=2,  # Depends on database
    ...
)

create_story(
    summary="Create UI components",
    execution_order=3,  # Can run after API
    ...
)
```

### Scenario 2: Fixing Existing Stories

If you have stories without execution_order:

```python
# 1. Run validation to find them
validate_backlog()

# Output shows:
# "❌ CRITICAL: 5 stories missing execution_order
#    → Affected tickets: SDT1-10, SDT1-11, SDT1-12, SDT1-13, SDT1-14"

# 2. Update each story (requires manual intervention or future update_issue enhancement)
# Note: Currently update_issue doesn't support execution_order
# You'll need to update via Jira UI or wait for feature enhancement

# 3. Verify fixes
validate_backlog()
```

### Scenario 3: Pre-Sprint Planning

```python
# Before sprint planning, ensure backlog is healthy
validate_backlog()

# If critical issues found, address them:
# - Add execution_order to stories
# - Link stories to epics
# - Estimate story points
# - Split over-sized stories

# Then proceed with sprint planning
list_sprints()
create_sprint(name="Sprint 23", goal="...")
add_issues_to_sprint(sprint_id=..., issue_keys=[...])
```

## Troubleshooting

### Q: Story was created but shows validation warnings

**A:** The story was created successfully, but validation detected issues. Review the warnings and consider updating the story to address them.

### Q: How do I update execution_order on existing stories?

**A:** Currently, you need to:
1. Update via Jira UI (Edit → Custom Fields → Execution Order)
2. Or wait for `update_issue` enhancement to support execution_order field

### Q: Validation says I need execution_order but I don't know what value to use

**A:** Consider:
1. Dependencies - Does this story depend on others? Give it a higher number.
2. Blockers - Do other stories depend on this? Give it a lower number.
3. Independence - Can it run in parallel? Any number works.
4. Epic sequence - Stories in same epic should be sequential.

Example:
```
Story A (foundation): execution_order=1
Story B (depends on A): execution_order=2
Story C (depends on A): execution_order=3
Story D (independent): execution_order=4
```

### Q: Can I disable validation?

**A:** Validation is informational and doesn't block story creation. However, stories without execution_order **will** block Orchestrator execution, so validation warnings should be addressed.

## Future Enhancements

Planned improvements:

1. **Auto-suggest execution_order** based on dependencies
2. **Dependency cycle detection** to catch circular dependencies
3. **Update issue tool enhancement** to support execution_order field
4. **Bulk validation fixes** to update multiple stories at once
5. **Custom validation rules** for project-specific requirements

## Support

For issues or questions:

1. Check the documentation: `docs/pm-agent-validation.md`
2. Review examples: `examples/pm_validation_example.py`
3. Run tests: `pytest tools/test_pm_validation.py -v`
4. Check validation logic: `tools/pm_validation.py`

## Summary

**Key Points:**

✅ **Always validate stories before creation**
✅ **execution_order is REQUIRED** (or Orchestrator can't execute)
✅ **Fix ERROR-level issues immediately**
✅ **Address WARNING-level issues for quality**
✅ **Use validate_backlog before sprint planning**

**Validation Flow:**

1. Call `validate_story` with story parameters
2. Check result for errors/warnings
3. Fix any critical issues
4. Create story with `create_story`
5. Story creation includes validation warnings in output

**Remember:** Validation helps maintain backlog quality and ensures successful sprint execution!
