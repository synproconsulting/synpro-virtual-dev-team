"""
Orchestrator Demo Script

This script demonstrates the orchestrator's resume capability
with a simulated sprint execution.
"""

import os
import sys
import time
from uuid import UUID

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from agents.orchestrator import Orchestrator
from agents.orchestrator_state import StateManager


def demo_basic_execution():
    """Demo: Basic sprint execution from start to finish."""
    print("=" * 80)
    print("DEMO 1: Basic Sprint Execution")
    print("=" * 80)
    
    # Create a mock orchestrator that simulates ticket execution
    class MockOrchestrator(Orchestrator):
        def get_sprint_tickets(self, sprint_id):
            """Return mock tickets."""
            return [
                {"key": "DEMO-1", "summary": "Setup project", "execution_order": 1},
                {"key": "DEMO-2", "summary": "Implement feature", "execution_order": 2},
                {"key": "DEMO-3", "summary": "Add tests", "execution_order": 3},
                {"key": "DEMO-4", "summary": "Deploy to staging", "execution_order": 4},
            ]
        
        def execute_ticket(self, ticket_key):
            """Simulate ticket execution."""
            print(f"  Executing {ticket_key}...")
            time.sleep(0.5)  # Simulate work
            return True
    
    with MockOrchestrator("DEMO", verbose=True) as orch:
        state_id = orch.start_sprint(
            sprint_id=1,
            sprint_name="Demo Sprint 1",
        )
        
        print(f"\n✓ Sprint completed successfully!")
        print(f"State ID: {state_id}")
        
        # Show final progress
        progress = orch.get_progress(state_id)
        print(f"\nFinal Progress:")
        print(f"  Completed: {progress['completed_tickets']}/{progress['total_tickets']}")
        print(f"  Failed: {progress['failed_tickets']}")
        print(f"  Progress: {progress['progress_percentage']}%")
    
    print()
    return state_id


def demo_execution_with_failure():
    """Demo: Sprint execution with ticket failures."""
    print("=" * 80)
    print("DEMO 2: Execution with Failures")
    print("=" * 80)
    
    class MockOrchestrator(Orchestrator):
        def get_sprint_tickets(self, sprint_id):
            return [
                {"key": "DEMO-5", "summary": "Task 1", "execution_order": 1},
                {"key": "DEMO-6", "summary": "Task 2 (will fail)", "execution_order": 2},
                {"key": "DEMO-7", "summary": "Task 3", "execution_order": 3},
                {"key": "DEMO-8", "summary": "Task 4 (will fail)", "execution_order": 4},
                {"key": "DEMO-9", "summary": "Task 5", "execution_order": 5},
            ]
        
        def execute_ticket(self, ticket_key):
            print(f"  Executing {ticket_key}...")
            time.sleep(0.3)
            
            # Simulate failures for specific tickets
            if ticket_key in ["DEMO-6", "DEMO-8"]:
                raise Exception(f"Simulated failure for {ticket_key}")
            
            return True
    
    with MockOrchestrator("DEMO", verbose=True) as orch:
        state_id = orch.start_sprint(
            sprint_id=2,
            sprint_name="Demo Sprint 2",
        )
        
        # Show final state
        progress = orch.get_progress(state_id)
        print(f"\n✓ Sprint completed with some failures")
        print(f"\nFinal Progress:")
        print(f"  Completed: {progress['completed_tickets']}/{progress['total_tickets']}")
        print(f"  Failed: {progress['failed_tickets']}")
        print(f"  Success rate: {progress['completed_tickets']/(progress['completed_tickets']+progress['failed_tickets'])*100:.1f}%")
    
    print()
    return state_id


def demo_pause_and_resume():
    """Demo: Pause execution and resume later."""
    print("=" * 80)
    print("DEMO 3: Pause and Resume")
    print("=" * 80)
    
    execution_count = {"count": 0}
    
    class MockOrchestrator(Orchestrator):
        def get_sprint_tickets(self, sprint_id):
            return [
                {"key": "DEMO-10", "summary": "Task 1", "execution_order": 1},
                {"key": "DEMO-11", "summary": "Task 2", "execution_order": 2},
                {"key": "DEMO-12", "summary": "Task 3 (pause here)", "execution_order": 3},
                {"key": "DEMO-13", "summary": "Task 4", "execution_order": 4},
                {"key": "DEMO-14", "summary": "Task 5", "execution_order": 5},
            ]
        
        def execute_ticket(self, ticket_key):
            execution_count["count"] += 1
            print(f"  Executing {ticket_key}...")
            time.sleep(0.3)
            
            # Simulate pause after 2 tickets on first run
            if execution_count["count"] == 2:
                print("\n  [Simulating interruption - pausing execution]")
                # In real scenario, this would be an external signal
                raise KeyboardInterrupt("Simulated pause")
            
            return True
    
    # First execution - will be interrupted
    print("\n--- First Execution (will be interrupted) ---")
    with MockOrchestrator("DEMO", verbose=True) as orch:
        try:
            state_id = orch.start_sprint(
                sprint_id=3,
                sprint_name="Demo Sprint 3",
            )
        except KeyboardInterrupt:
            # Get the state from the last sprint (will be the most recent one)
            with StateManager() as sm:
                state = sm.get_latest_state_for_sprint(3)
                state_id = state.id
                sm.pause_execution(state_id, "Interrupted during demo")
            
            print(f"\n✓ Execution paused at state: {state_id}")
    
    # Show progress after pause
    with MockOrchestrator("DEMO", verbose=False) as orch:
        progress = orch.get_progress(state_id)
        print(f"\nProgress after pause:")
        print(f"  Status: {progress['status']}")
        print(f"  Completed: {progress['completed_tickets']}/{progress['total_tickets']}")
        print(f"  Remaining: {progress['remaining_tickets']}")
    
    # Resume execution
    print("\n--- Resuming Execution ---")
    time.sleep(1)
    
    with MockOrchestrator("DEMO", verbose=True) as orch:
        orch.resume_sprint(state_id)
    
    # Show final progress
    with MockOrchestrator("DEMO", verbose=False) as orch:
        progress = orch.get_progress(state_id)
        print(f"\n✓ Execution resumed and completed!")
        print(f"\nFinal Progress:")
        print(f"  Status: {progress['status']}")
        print(f"  Completed: {progress['completed_tickets']}/{progress['total_tickets']}")
        print(f"  Progress: {progress['progress_percentage']}%")
    
    print()
    return state_id


def demo_list_resumable():
    """Demo: List all resumable executions."""
    print("=" * 80)
    print("DEMO 4: List Resumable Executions")
    print("=" * 80)
    
    with Orchestrator("DEMO", verbose=False) as orch:
        resumable = orch.list_resumable()
        
        if not resumable:
            print("\nNo resumable executions found.")
            print("(This is expected if all demos completed successfully)")
        else:
            print(f"\nFound {len(resumable)} resumable execution(s):")
            for item in resumable:
                print(f"\n  State ID: {item['state_id']}")
                print(f"  Sprint: {item['sprint_name']} (ID: {item['sprint_id']})")
                print(f"  Status: {item['status']}")
                print(f"  Progress: {item['completed']}/{item['total_tickets']} completed, "
                      f"{item['remaining']} remaining")
    
    print()


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("ORCHESTRATOR RESUME CAPABILITY - DEMO")
    print("=" * 80)
    print("\nThis demo showcases the orchestrator's ability to:")
    print("  1. Execute sprints sequentially")
    print("  2. Handle failures gracefully")
    print("  3. Pause and resume execution")
    print("  4. Track progress throughout")
    print("\n" + "=" * 80 + "\n")
    
    input("Press Enter to start Demo 1: Basic Execution...")
    demo_basic_execution()
    
    input("Press Enter to start Demo 2: Execution with Failures...")
    demo_execution_with_failure()
    
    input("Press Enter to start Demo 3: Pause and Resume...")
    demo_pause_and_resume()
    
    input("Press Enter to start Demo 4: List Resumable Executions...")
    demo_list_resumable()
    
    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print("\nAll demos completed successfully!")
    print("\nNext steps:")
    print("  - Check the database for orchestrator_states records")
    print("  - Try the CLI: python agents/orchestrator_cli.py list --project DEMO")
    print("  - Review docs/orchestrator_resume_capability.md for more details")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n✗ Demo error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
