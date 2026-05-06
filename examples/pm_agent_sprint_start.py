#!/usr/bin/env python3
"""
examples/pm_agent_sprint_start.py
──────────────────────────────────
Example demonstrating the PM Agent sprint start workflow (SDT1-73).

This example shows how the PM Agent:
1. Creates a sprint
2. Populates it with stories
3. Sets execution order on all stories
4. Requests approval
5. Starts the sprint on approval

Usage:
    python examples/pm_agent_sprint_start.py
"""

import os
import sys
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crewai import Task, Crew
from agents.pm_agent import build_pm_agent
from tools.pm_tools import ALL_PM_TOOLS


def create_sprint_planning_task() -> Task:
    """Create a task for sprint planning with approval and start workflow."""
    return Task(
        description="""
        You are planning a new sprint for the authentication feature. Follow this workflow:
        
        1. REVIEW BACKLOG
           - List all open issues in the backlog
           - Identify stories related to authentication
        
        2. CREATE SPRINT
           - Create a new sprint called "Sprint 1 - Authentication"
           - Set the sprint goal to "Implement user authentication and registration"
        
        3. POPULATE SPRINT
           - Add relevant authentication stories to the sprint
           - Ensure all stories have:
             * Clear descriptions
             * Story point estimates
             * Execution order set based on dependencies
             * Epic linkage
        
        4. VERIFY READINESS
           - Confirm all stories have execution_order set (customfield_10071)
           - Check for any missing dependencies or blockers
           - Verify total story points are within sprint capacity (20-40 points)
        
        5. REQUEST APPROVAL
           - Present the sprint plan with:
             * List of stories with execution order
             * Total story points
             * Sprint goal
             * Any risks or dependencies
           - Wait for explicit "approve" or "yes" response
        
        6. START SPRINT (only after approval)
           - Use start_sprint tool to activate the sprint
           - Confirm the sprint is now in 'active' state
           - Report success to the user
        
        IMPORTANT: 
        - Do NOT start the sprint without explicit approval
        - Always set execution_order on every story before adding to sprint
        - Verify the sprint state is 'future' before attempting to start it
        """,
        expected_output="""
        A detailed sprint plan including:
        - Sprint ID and name
        - List of stories with execution order
        - Total story points
        - Sprint state (should be 'active' after approval)
        - Confirmation message that work can begin
        """,
        agent=None,  # Will be set when creating the crew
    )


def simulate_approval_workflow():
    """Simulate the sprint approval and start workflow."""
    print("=" * 80)
    print("PM Agent Sprint Start Workflow Example (SDT1-73)")
    print("=" * 80)
    print()
    
    # Build the PM Agent with all tools
    pm_agent = build_pm_agent(verbose=True, tools=ALL_PM_TOOLS)
    
    # Create the sprint planning task
    task = create_sprint_planning_task()
    task.agent = pm_agent
    
    print("Step 1: PM Agent will plan the sprint...")
    print("-" * 80)
    print()
    
    # In a real scenario, this would interact with Jira
    # For this example, we'll demonstrate the workflow steps
    
    print("Example workflow:")
    print()
    print("1. PM Agent reviews backlog")
    print("   → list_backlog()")
    print()
    print("2. PM Agent creates sprint")
    print("   → create_sprint(name='Sprint 1 - Authentication', goal='Implement user auth')")
    print("   → Result: Sprint ID = 123, State = 'future'")
    print()
    print("3. PM Agent adds stories with execution order")
    print("   → create_story('Implement login API', execution_order=1)")
    print("   → create_story('Add JWT authentication', execution_order=2)")
    print("   → create_story('Create user registration', execution_order=3)")
    print("   → add_issues_to_sprint(sprint_id=123, issue_keys=[...])")
    print()
    print("4. PM Agent presents sprint plan")
    print("   ┌─────────────────────────────────────────────────────────────┐")
    print("   │ Sprint 1 - Authentication                                   │")
    print("   │                                                             │")
    print("   │ Stories:                                                    │")
    print("   │  1. [SDT1-45] Implement login API (5 pts)                  │")
    print("   │  2. [SDT1-46] Add JWT authentication (8 pts)               │")
    print("   │  3. [SDT1-47] Create user registration (5 pts)             │")
    print("   │                                                             │")
    print("   │ Total: 18 story points                                      │")
    print("   │ State: future                                               │")
    print("   │                                                             │")
    print("   │ All stories have execution_order set ✓                     │")
    print("   │ No blockers ✓                                               │")
    print("   │                                                             │")
    print("   │ Ready to start. Approve? (yes/no)                          │")
    print("   └─────────────────────────────────────────────────────────────┘")
    print()
    print("5. User approves: 'yes'")
    print()
    print("6. PM Agent starts the sprint")
    print("   → start_sprint(sprint_id=123)")
    print("   → Result:")
    print()
    print("   ✓ Sprint started successfully!")
    print("     Sprint ID: 123")
    print("     Name: Sprint 1 - Authentication")
    print("     State: active")
    print("     Goal: Implement user authentication and registration")
    print()
    print("7. Sprint is now active and ready for development team")
    print()
    print("=" * 80)
    print("Workflow Complete!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  - Orchestrator can pick up the active sprint")
    print("  - Development team can start working on SDT1-45")
    print("  - PM Agent monitors progress and updates stakeholders")
    print()


def demonstrate_error_handling():
    """Demonstrate error handling in the sprint start workflow."""
    print()
    print("=" * 80)
    print("Error Handling Examples")
    print("=" * 80)
    print()
    
    print("Scenario 1: Sprint already active")
    print("-" * 40)
    print("→ start_sprint(sprint_id=123)")
    print("✗ Failed to start sprint: Sprint 123 is already active")
    print()
    
    print("Scenario 2: Sprint is closed")
    print("-" * 40)
    print("→ start_sprint(sprint_id=999)")
    print("✗ Failed to start sprint: Sprint 999 is closed and cannot be started")
    print()
    
    print("Scenario 3: Missing execution_order on stories")
    print("-" * 40)
    print("PM Agent should detect this BEFORE starting the sprint:")
    print("⚠️  WARNING: Story SDT1-50 does not have execution_order set")
    print("⚠️  Cannot start sprint - fix execution_order first")
    print()
    
    print("Scenario 4: No approval given")
    print("-" * 40)
    print("PM Agent: 'Ready to start. Approve? (yes/no)'")
    print("User: 'not yet'")
    print("PM Agent: 'Understood. Sprint remains in future state.'")
    print("→ start_sprint NOT called")
    print()


def show_integration_with_orchestrator():
    """Show how the started sprint integrates with the Orchestrator."""
    print()
    print("=" * 80)
    print("Integration with Orchestrator")
    print("=" * 80)
    print()
    
    print("After PM Agent starts the sprint, the Orchestrator can execute it:")
    print()
    print("from agents.orchestrator import start_sprint_execution")
    print()
    print("state_id = start_sprint_execution(")
    print("    sprint_id=123,")
    print("    sprint_name='Sprint 1 - Authentication',")
    print("    jira_project_key='SDT1'")
    print(")")
    print()
    print("Orchestrator workflow:")
    print("  1. Fetch 'To Do' stories from sprint 123")
    print("  2. Sort by execution_order (customfield_10071)")
    print("  3. Execute SDT1-45 → SDT1-46 → SDT1-47 in sequence")
    print("  4. Track progress in orchestrator_states table")
    print("  5. Handle failures and support resume capability")
    print()


if __name__ == "__main__":
    # Check if environment variables are set
    required_vars = ["JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("Warning: Missing environment variables:", ", ".join(missing_vars))
        print("This example will run in simulation mode.")
        print()
    
    # Run the demonstrations
    simulate_approval_workflow()
    demonstrate_error_handling()
    show_integration_with_orchestrator()
    
    print()
    print("For more information, see:")
    print("  - docs/sprint-start-workflow.md")
    print("  - uat/backend/tests/test_pm_sprint_start.py")
    print("  - agents/pm_agent.py")
    print("  - tools/pm_tools.py")
