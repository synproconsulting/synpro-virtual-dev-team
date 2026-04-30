"""
Example: Using Manager Agent for Jira workflow transitions.

This script demonstrates how to use the Manager Agent to transition
Jira issues through their workflow with exponential backoff retry logic.
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from manager_agent import create_manager_agent, TransitionStatus


async def example_single_transition():
    """Example: Transition a single issue."""
    print("\n=== Single Transition Example ===\n")
    
    agent = create_manager_agent()
    
    # Start work on an issue
    print("Starting work on SDT1-44...")
    result = await agent.start_work(
        issue_key="SDT1-44",
        assignee="developer-bot",
        comment="Manager Agent starting work on this ticket"
    )
    
    if result.status == TransitionStatus.SUCCESS:
        print(f"✓ Success! Transitioned to '{result.final_status}'")
        print(f"  - Attempts: {result.attempts}")
        print(f"  - Time: {result.total_time:.2f}s")
    else:
        print(f"✗ Failed: {result.error_message}")
        print(f"  - Attempts: {result.attempts}")


async def example_workflow_sequence():
    """Example: Complete workflow sequence for an issue."""
    print("\n=== Workflow Sequence Example ===\n")
    
    agent = create_manager_agent(max_retries=3, base_delay=0.5)
    issue_key = "SDT1-45"
    
    # 1. Start work
    print(f"1. Starting work on {issue_key}...")
    result = await agent.start_work(issue_key, assignee="dev-agent")
    print(f"   Status: {result.final_status}")
    
    if result.status != TransitionStatus.SUCCESS:
        print(f"   Failed: {result.error_message}")
        return
    
    # 2. Move to code review
    print(f"2. Moving {issue_key} to code review...")
    result = await agent.move_to_code_review(
        issue_key,
        comment="Implementation complete, ready for review"
    )
    print(f"   Status: {result.final_status}")
    
    # 3. Move to testing
    print(f"3. Moving {issue_key} to testing...")
    result = await agent.move_to_testing(
        issue_key,
        comment="Code review passed, ready for QA"
    )
    print(f"   Status: {result.final_status}")
    
    # 4. Complete work
    print(f"4. Completing {issue_key}...")
    result = await agent.complete_work(
        issue_key,
        comment="All tests passed, ticket complete"
    )
    print(f"   Status: {result.final_status}")
    print(f"   Total attempts across workflow: {result.attempts}")


async def example_bulk_transitions():
    """Example: Bulk transition multiple issues."""
    print("\n=== Bulk Transition Example ===\n")
    
    agent = create_manager_agent()
    
    transitions = [
        {
            "issue_key": "SDT1-44",
            "target_status": "In Progress",
            "comment": "Starting work",
        },
        {
            "issue_key": "SDT1-45",
            "target_status": "In Progress",
            "comment": "Starting work",
        },
        {
            "issue_key": "SDT1-46",
            "target_status": "Code Review",
            "comment": "Ready for review",
        },
    ]
    
    print(f"Transitioning {len(transitions)} issues...")
    results = await agent.client.bulk_transition(transitions)
    
    successful = sum(1 for r in results if r.status == TransitionStatus.SUCCESS)
    failed = len(results) - successful
    
    print(f"\nResults:")
    print(f"  ✓ Successful: {successful}")
    print(f"  ✗ Failed: {failed}")
    
    for result in results:
        status_icon = "✓" if result.status == TransitionStatus.SUCCESS else "✗"
        print(f"  {status_icon} {result.issue_key}: {result.final_status or result.error_message}")


async def example_custom_transition():
    """Example: Custom transition with specific parameters."""
    print("\n=== Custom Transition Example ===\n")
    
    agent = create_manager_agent()
    
    # Get current status first
    print("Getting current status...")
    current_status = await agent.get_issue_status("SDT1-44")
    print(f"Current status: {current_status}")
    
    # Transition by status name
    print("\nTransitioning to 'In Progress'...")
    result = await agent.client.transition_issue_by_name(
        issue_key="SDT1-44",
        target_status="In Progress",
        fields={
            "assignee": {"name": "john.doe"},
            "priority": {"name": "High"},
        },
        comment="High priority work started by Manager Agent"
    )
    
    if result.status == TransitionStatus.SUCCESS:
        print(f"✓ Transitioned successfully")
        print(f"  - Transition: {result.transition_name}")
        print(f"  - Final status: {result.final_status}")
        print(f"  - Attempts: {result.attempts}")
        print(f"  - Time: {result.total_time:.2f}s")
    else:
        print(f"✗ Transition failed: {result.error_message}")


async def example_error_handling():
    """Example: Handling errors and retries."""
    print("\n=== Error Handling Example ===\n")
    
    agent = create_manager_agent(max_retries=3)
    
    # Try to transition to an invalid status
    print("Attempting to transition to invalid status...")
    result = await agent.client.transition_issue_by_name(
        issue_key="SDT1-44",
        target_status="Invalid Status",
    )
    
    if result.status == TransitionStatus.FAILED:
        print(f"✗ Expected failure occurred")
        print(f"  - Error: {result.error_message}")
        print(f"  - Attempts: {result.attempts}")
    
    # Try with a non-existent issue
    print("\nAttempting to get status of non-existent issue...")
    status = await agent.get_issue_status("SDT1-9999")
    
    if status is None:
        print("✗ Issue not found (expected)")


async def main():
    """Run all examples."""
    print("=" * 60)
    print("Manager Agent Workflow Examples")
    print("=" * 60)
    
    # Check environment variables
    required_vars = ["JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"\n⚠ Missing environment variables: {', '.join(missing)}")
        print("Please set these before running examples:")
        for var in missing:
            print(f"  export {var}=your-value")
        return
    
    try:
        # Run examples
        await example_single_transition()
        await asyncio.sleep(1)  # Brief pause between examples
        
        await example_workflow_sequence()
        await asyncio.sleep(1)
        
        await example_bulk_transitions()
        await asyncio.sleep(1)
        
        await example_custom_transition()
        await asyncio.sleep(1)
        
        await example_error_handling()
        
        print("\n" + "=" * 60)
        print("Examples complete!")
        print("=" * 60)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
