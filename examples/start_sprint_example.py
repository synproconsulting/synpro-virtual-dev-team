"""
examples/start_sprint_example.py
─────────────────────────────────
Example script demonstrating PM Agent sprint starting capability.

This script shows the complete workflow:
1. Create a sprint
2. Add stories to the sprint
3. Start the sprint upon approval
4. Notify the team

Usage:
    python examples/start_sprint_example.py
"""

import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.jira_client import (
    create_sprint,
    add_issues_to_sprint,
    start_sprint,
    add_comment,
    list_sprints,
)


def format_iso_date(days_from_now: int) -> str:
    """Generate ISO-8601 formatted date string.
    
    Args:
        days_from_now: Number of days from today
    
    Returns:
        ISO-8601 formatted date string
    """
    target_date = datetime.now() + timedelta(days=days_from_now)
    return target_date.strftime("%Y-%m-%dT09:00:00.000Z")


def create_and_start_sprint_example():
    """Example: Create, populate, and start a sprint."""
    
    print("=" * 70)
    print("PM Agent Sprint Starting Example")
    print("=" * 70)
    print()
    
    # Step 1: List existing sprints
    print("Step 1: Checking existing sprints...")
    try:
        sprints = list_sprints()
        print(f"Found {len(sprints)} active/future sprints:")
        for sprint in sprints:
            print(f"  - [{sprint['id']}] {sprint['name']} (state: {sprint['state']})")
        print()
    except Exception as e:
        print(f"Error listing sprints: {e}")
        print()
    
    # Step 2: Create a new sprint
    print("Step 2: Creating new sprint...")
    try:
        sprint_name = f"Sprint Demo - {datetime.now().strftime('%Y-%m-%d')}"
        sprint_goal = "Demonstrate sprint starting capability"
        start_date = format_iso_date(0)  # Today
        end_date = format_iso_date(14)   # 2 weeks from now
        
        sprint_result = create_sprint(
            name=sprint_name,
            goal=sprint_goal,
            start_date=start_date,
            end_date=end_date
        )
        
        sprint_id = sprint_result["id"]
        print(f"✓ Created sprint: {sprint_name}")
        print(f"  ID: {sprint_id}")
        print(f"  State: {sprint_result['state']}")
        print(f"  Goal: {sprint_goal}")
        print()
    except Exception as e:
        print(f"✗ Error creating sprint: {e}")
        return
    
    # Step 3: Add issues to the sprint
    print("Step 3: Adding issues to sprint...")
    print("  Note: Using example issue keys - replace with real keys from your project")
    
    # Replace these with real issue keys from your Jira project
    example_issues = ["SDT1-1", "SDT1-2", "SDT1-3"]
    
    try:
        add_issues_to_sprint(sprint_id, example_issues)
        print(f"✓ Added {len(example_issues)} issues to sprint {sprint_id}")
        for issue_key in example_issues:
            print(f"  - {issue_key}")
        print()
    except Exception as e:
        print(f"⚠️  Warning: Could not add issues (this is normal if example keys don't exist)")
        print(f"   Error: {e}")
        print()
    
    # Step 4: Simulate approval checkpoint
    print("Step 4: Sprint approval checkpoint...")
    print("  In a real workflow, you would:")
    print("  - Review sprint contents")
    print("  - Verify all stories have execution_order")
    print("  - Check dependencies are documented")
    print("  - Get stakeholder approval")
    print()
    
    approval = input("  Approve sprint start? (y/n): ").strip().lower()
    print()
    
    if approval != 'y':
        print("Sprint start cancelled by user.")
        print("Sprint remains in 'future' state and can be started later.")
        return
    
    # Step 5: Start the sprint
    print("Step 5: Starting sprint...")
    try:
        start_result = start_sprint(sprint_id)
        
        print(f"✓ Sprint started successfully!")
        print(f"  Name: {start_result['name']}")
        print(f"  State: {start_result['state']}")
        print(f"  Start: {start_result.get('start_date', 'Not set')}")
        print(f"  End: {start_result.get('end_date', 'Not set')}")
        print()
        
    except ValueError as e:
        print(f"✗ Failed to start sprint: {e}")
        print()
        return
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        print()
        return
    
    # Step 6: Post notification comment
    print("Step 6: Posting sprint start notification...")
    try:
        # Post comment on the first issue in the sprint
        if example_issues:
            comment_body = (
                f"Sprint {sprint_name} is now ACTIVE.\n\n"
                f"Goal: {sprint_goal}\n"
                f"Duration: {start_date} to {end_date}\n\n"
                f"Development team can begin work on stories in execution_order."
            )
            
            # Note: This will fail if the issue key doesn't exist
            # In production, you'd post on the sprint's epic or main story
            print(f"  (Would post to {example_issues[0]} if it existed)")
            print(f"  Comment: {comment_body}")
            print()
    except Exception as e:
        print(f"⚠️  Could not post comment: {e}")
        print()
    
    # Summary
    print("=" * 70)
    print("Sprint Starting Complete!")
    print("=" * 70)
    print(f"Sprint ID: {sprint_id}")
    print(f"Sprint Name: {sprint_name}")
    print(f"State: active")
    print()
    print("Next steps:")
    print("  1. Orchestrator can now process this sprint")
    print("  2. Development team receives Jira notifications")
    print("  3. Stories will be executed in execution_order")
    print()


def start_existing_sprint_example():
    """Example: Start an existing sprint by ID."""
    
    print("=" * 70)
    print("Start Existing Sprint")
    print("=" * 70)
    print()
    
    # List available sprints
    try:
        sprints = list_sprints()
        future_sprints = [s for s in sprints if s['state'] == 'future']
        
        if not future_sprints:
            print("No sprints in 'future' state to start.")
            print("Create a new sprint first using the main example.")
            return
        
        print("Available sprints to start:")
        for sprint in future_sprints:
            print(f"  [{sprint['id']}] {sprint['name']}")
            if sprint.get('goal'):
                print(f"      Goal: {sprint['goal']}")
        print()
        
        sprint_id = input("Enter sprint ID to start: ").strip()
        
        if not sprint_id.isdigit():
            print("Invalid sprint ID")
            return
        
        sprint_id = int(sprint_id)
        
        # Start the sprint
        print(f"\nStarting sprint {sprint_id}...")
        result = start_sprint(sprint_id)
        
        print(f"✓ Sprint started: {result['name']}")
        print(f"  State: {result['state']}")
        print()
        
    except ValueError as e:
        print(f"✗ Error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


def main():
    """Main entry point."""
    
    # Check environment variables
    required_vars = ["JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY", "JIRA_BOARD_ID"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print()
        print("Please set these variables in your .env file or environment.")
        return
    
    print()
    print("Choose an example:")
    print("  1. Create and start a new sprint (full workflow)")
    print("  2. Start an existing sprint")
    print("  3. Exit")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    print()
    
    if choice == "1":
        create_and_start_sprint_example()
    elif choice == "2":
        start_existing_sprint_example()
    elif choice == "3":
        print("Goodbye!")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
