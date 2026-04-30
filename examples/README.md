# PM Agent Examples

This directory contains example scripts demonstrating PM Agent capabilities.

## Prerequisites

Set the following environment variables before running any examples:

```bash
export JIRA_URL="https://yourcompany.atlassian.net"
export JIRA_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your-jira-api-token"
export JIRA_PROJECT_KEY="PROJ"
export JIRA_BOARD_ID="123"
```

To get a Jira API token:
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name and copy the token

## Examples

### pm_agent_dependencies_example.py

Demonstrates how to create stories with dependencies using blocker links.

**What it does:**
1. Creates an Epic for "User Profile Management"
2. Creates 4 stories with dependencies:
   - Story A: Database schema (execution_order=1)
   - Story B: GET endpoint (execution_order=2, blocked by A)
   - Story C: PUT endpoint (execution_order=3, blocked by B)
   - Story D: Frontend UI (execution_order=4, blocked by B and C)
3. Creates "blocks" links between dependent stories
4. Adds explanatory comments
5. Verifies all links were created correctly

**Run it:**
```bash
python examples/pm_agent_dependencies_example.py
```

**Expected Output:**
```
================================================================================
PM Agent Dependencies Example
================================================================================

Step 1: Creating Epic...
✓ Created Epic: PROJ-123

Step 2: Creating Story A (Database Schema)...
✓ Created Story A: PROJ-124 (execution_order=1)

...

✓ All stories created with proper dependencies and execution order
```

## Adding New Examples

When creating new examples:

1. Use clear, descriptive names
2. Include docstrings explaining what the example demonstrates
3. Check for required environment variables at startup
4. Print clear progress messages
5. Handle errors gracefully
6. Update this README with your example

## Related Documentation

- [Jira Issue Links Documentation](../docs/jira-issue-links.md)
- [PM Agent Documentation](../agents/pm_agent.py)
- [PM Tools API](../tools/pm_tools.py)
