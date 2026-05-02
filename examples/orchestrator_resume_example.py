#!/usr/bin/env python3
"""
Example demonstrating orchestrator state persistence and resume functionality.

This script shows how to:
1. Start sprint execution
2. Simulate a crash
3. Resume from the last checkpoint
4. Monitor progress
5. Handle failures gracefully

Run this example:
    python examples/orchestrator_resume_example.py
"""

import sys
import os
import time
from uuid import UUID

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../uat/backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import SessionLocal, init_database
from agents.orchestrator import Orchestrator
from agents.orchestrator_state import StateManager


def example_1_basic_start_and_complete():
    """Example 1: Basic sprint start and completion."""
    print("=" * 70)
    print("Example 1: Basic Sprint Execution")
    print("=" * 70)
    print()
    
    # Initialize database
    init_database()
    
    with Orchestrator("SDT1", verbose=True) as orchestrator:
        # Mock ticket data (in production, this comes from Jira)
        with SessionLocal() as db:
            from unittest.mock import patch
            
            mock_tickets = [
                {"key": "SDT1-101", "summary": "Setup database", "execution_order": 1},
                {"key": "SDT1-102", "summary": "Create API endpoints", "execution_order": 2},
                {"key": "SDT1-103", "summary": "Add authentication", "execution_order": 3},
            ]
            
            with patch.object(orchestrator, 'get_sprint_tickets', return_value=mock_tickets):
                with patch.object(orchestrator, 'execute_ticket', return_value=True):
                    state_id = orchestrator.start_sprint(
                        sprint_id=42,
                        sprint_name="Sprint 42",
                    )
            
            print()
            print(f"Sprint completed! State ID: {state_id}")
            
            # Show final progress
            progress = orchestrator.get_progress(state_id)
            print(f"Final progress: {progress['progress_percentage']}%")
            print(f"Completed: {progress['completed_tickets']} tickets")
    
    print()


def example_2_resume_after_simulated_crash():
    """Example 2: Resume execution after a simulated crash."""
    print("=" * 70)
    print("Example 2: Resume After Crash")
    print("=" * 70)
    print()
    
    # Initialize database
    init_database()
    
    # Create a state with some completed and some remaining tickets
    with SessionLocal() as db:
        state_manager = StateManager(db=db)
        
        # Simulate a sprint that was interrupted
        state = state_manager.create_state(
            sprint_id=43,
            sprint_name="Sprint 43",
            jira_project_key="SDT1",
            ticket_queue=["SDT1-203", "SDT1-204", "SDT1-205"],
        )
        
        # Mark as started
        state_manager.start_execution(state.id)
        
        # Simulate some completed tickets
        state_manager.checkpoint(
            state.id,
            completed_tickets=["SDT1-201", "SDT1-202"],
        )
        
        # Simulate a crash (mark as failed)
        state_manager.fail_execution(
            state.id,
            "Simulated crash during execution",
        )
        
        print(f"Created crashed sprint state: {state.id}")
        print()
        
        state_id = state.id
    
    # Now resume execution
    print("Resuming execution...")
    print()
    
    with Orchestrator("SDT1", verbose=True) as orchestrator:
        from unittest.mock import patch
        
        with patch.object(orchestrator, 'execute_ticket', return_value=True):
            orchestrator.resume_sprint(state_id)
        
        print()
        print("Sprint resumed and completed!")
        
        # Show final progress
        progress = orchestrator.get_progress(state_id)
        print(f"Final progress: {progress['progress_percentage']}%")
        print(f"Completed: {progress['completed_tickets']} tickets")
    
    print()


def example_3_manual_pause_and_resume():
    """Example 3: Manual pause and resume."""
    print("=" * 70)
    print("Example 3: Manual Pause and Resume")
    print("=" * 70)
    print()
    
    # Initialize database
    init_database()
    
    # Create a state
    with SessionLocal() as db:
        state_manager = StateManager(db=db)
        
        state = state_manager.create_state(
            sprint_id=44,
            sprint_name="Sprint 44",
            jira_project_key="SDT1",
            ticket_queue=["SDT1-301", "SDT1-302"],
        )
        
        state_manager.start_execution(state.id)
        
        print(f"Created sprint: {state.id}")
        print()
        
        state_id = state.id
    
    # Pause the sprint
    print("Pausing sprint for maintenance...")
    with Orchestrator("SDT1", verbose=False) as orchestrator:
        orchestrator.pause(state_id, "Simulated maintenance window")
    
    print("Sprint paused.")
    print()
    
    # Simulate waiting
    print("Performing maintenance...")
    time.sleep(1)
    print("Maintenance complete.")
    print()
    
    # Resume execution
    print("Resuming sprint...")
    print()
    
    with Orchestrator("SDT1", verbose=True) as orchestrator:
        from unittest.mock import patch
        
        with patch.object(orchestrator, 'execute_ticket', return_value=True):
            orchestrator.resume_sprint(state_id)
        
        print()
        print("Sprint completed after resume!")
    
    print()


def example_4_list_resumable():
    """Example 4: List all resumable sprints."""
    print("=" * 70)
    print("Example 4: List Resumable Sprints")
    print("=" * 70)
    print()
    
    # Initialize database
    init_database()
    
    # Create several states with different statuses
    with SessionLocal() as db:
        state_manager = StateManager(db=db)
        
        # Paused state
        state1 = state_manager.create_state(
            sprint_id=50,
            sprint_name="Sprint 50 - Paused",
            jira_project_key="SDT1",
            ticket_queue=["SDT1-501", "SDT1-502"],
        )
        state_manager.start_execution(state1.id)
        state_manager.pause_execution(state1.id, "Waiting for external dependency")
        
        # Failed state
        state2 = state_manager.create_state(
            sprint_id=51,
            sprint_name="Sprint 51 - Failed",
            jira_project_key="SDT1",
            ticket_queue=["SDT1-511"],
        )
        state_manager.start_execution(state2.id)
        state_manager.fail_execution(state2.id, "Network timeout")
        
        # Completed state (should not appear in resumable list)
        state3 = state_manager.create_state(
            sprint_id=52,
            sprint_name="Sprint 52 - Completed",
            jira_project_key="SDT1",
            ticket_queue=[],
        )
        state_manager.complete_execution(state3.id)
    
    # List resumable
    with Orchestrator("SDT1", verbose=False) as orchestrator:
        resumable = orchestrator.list_resumable()
    
    print(f"Found {len(resumable)} resumable sprint(s):")
    print()
    
    for sprint in resumable:
        print(f"Sprint #{sprint['sprint_id']}: {sprint['sprint_name']}")
        print(f"  State ID: {sprint['state_id']}")
        print(f"  Status:   {sprint['status'].upper()}")
        print(f"  Progress: {sprint['completed']}/{sprint['total_tickets']} completed, "
              f"{sprint['remaining']} remaining")
        print()
    
    print()


def example_5_progress_monitoring():
    """Example 5: Monitor progress during execution."""
    print("=" * 70)
    print("Example 5: Progress Monitoring")
    print("=" * 70)
    print()
    
    # Initialize database
    init_database()
    
    with SessionLocal() as db:
        state_manager = StateManager(db=db)
        
        # Create a sprint with several tickets
        state = state_manager.create_state(
            sprint_id=60,
            sprint_name="Sprint 60",
            jira_project_key="SDT1",
            ticket_queue=["SDT1-601", "SDT1-602", "SDT1-603", "SDT1-604", "SDT1-605"],
        )
        state_manager.start_execution(state.id)
        
        state_id = state.id
        
        print(f"Created sprint: {state_id}")
        print()
        
        # Simulate processing tickets one by one
        tickets = ["SDT1-601", "SDT1-602", "SDT1-603", "SDT1-604", "SDT1-605"]
        
        for i, ticket in enumerate(tickets):
            # Mark ticket in progress
            state_manager.checkpoint(state_id, current_ticket=ticket)
            
            # Get and display progress
            progress = state_manager.get_progress(state_id)
            print(f"Processing: {ticket}")
            print(f"  Progress: {progress['progress_percentage']:.1f}% "
                  f"({progress['completed_tickets']}/{progress['total_tickets']})")
            
            # Simulate work
            time.sleep(0.5)
            
            # Mark completed
            state_manager.mark_ticket_completed(state_id, ticket)
            print(f"  ✓ Completed")
            print()
        
        # Final state
        state_manager.complete_execution(state_id)
        
        progress = state_manager.get_progress(state_id)
        print(f"Sprint completed!")
        print(f"Final progress: {progress['progress_percentage']}%")
    
    print()


def example_6_handling_failures():
    """Example 6: Handle ticket failures gracefully."""
    print("=" * 70)
    print("Example 6: Handling Ticket Failures")
    print("=" * 70)
    print()
    
    # Initialize database
    init_database()
    
    with SessionLocal() as db:
        state_manager = StateManager(db=db)
        
        state = state_manager.create_state(
            sprint_id=70,
            sprint_name="Sprint 70",
            jira_project_key="SDT1",
            ticket_queue=["SDT1-701", "SDT1-702", "SDT1-703"],
        )
        state_manager.start_execution(state.id)
        
        state_id = state.id
        
        print(f"Created sprint: {state_id}")
        print()
        
        # Process tickets, with one failing
        print("Processing SDT1-701...")
        state_manager.checkpoint(state_id, current_ticket="SDT1-701")
        time.sleep(0.3)
        state_manager.mark_ticket_completed(state_id, "SDT1-701")
        print("✓ SDT1-701 completed")
        print()
        
        print("Processing SDT1-702...")
        state_manager.checkpoint(state_id, current_ticket="SDT1-702")
        time.sleep(0.3)
        state_manager.mark_ticket_failed(
            state_id,
            "SDT1-702",
            "ValueError: Invalid configuration in feature flag settings",
        )
        print("✗ SDT1-702 failed!")
        print()
        
        print("Processing SDT1-703...")
        state_manager.checkpoint(state_id, current_ticket="SDT1-703")
        time.sleep(0.3)
        state_manager.mark_ticket_completed(state_id, "SDT1-703")
        print("✓ SDT1-703 completed")
        print()
        
        # Complete execution
        state_manager.complete_execution(state_id)
        
        # Show summary
        state = state_manager.get_state(state_id)
        progress = state_manager.get_progress(state_id)
        
        print("Sprint completed with failures:")
        print(f"  Completed: {progress['completed_tickets']} tickets")
        print(f"  Failed:    {progress['failed_tickets']} tickets")
        print()
        
        if state.failed_tickets:
            print("Failed tickets:")
            for failure in state.failed_tickets:
                print(f"  • {failure['ticket_key']}: {failure['error_message']}")
        
    print()


def main():
    """Run all examples."""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 10 + "Orchestrator Resume Functionality Examples" + " " * 16 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    try:
        # Run each example
        example_1_basic_start_and_complete()
        example_2_resume_after_simulated_crash()
        example_3_manual_pause_and_resume()
        example_4_list_resumable()
        example_5_progress_monitoring()
        example_6_handling_failures()
        
        print("=" * 70)
        print("All examples completed successfully!")
        print("=" * 70)
        print()
        
    except Exception as e:
        print(f"\n✗ Example failed with error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
