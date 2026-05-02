#!/usr/bin/env python3
"""
examples/orchestrator_crash_recovery_demo.py
────────────────────────────────────────────
Demo script showing orchestrator crash recovery capabilities.

This script demonstrates:
1. Starting a sprint execution
2. Simulating a crash during execution
3. Resuming from the last checkpoint
4. Handling ticket failures
5. Checking progress and status

Usage:
    python examples/orchestrator_crash_recovery_demo.py
"""

import sys
import os
import time
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../uat/backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, OrchestratorStatus
from agents.orchestrator import Orchestrator
from agents.orchestrator_state import StateManager


def setup_test_database():
    """Create in-memory database for demo."""
    print("Setting up test database...")
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine)
    return TestSessionLocal()


def print_section(title):
    """Print a section header."""
    print()
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)
    print()


def print_state(state_manager, state_id):
    """Print current state information."""
    progress = state_manager.get_progress(state_id)
    
    print(f"State ID:        {progress['state_id']}")
    print(f"Sprint:          {progress['sprint_name']} (ID: {progress['sprint_id']})")
    print(f"Status:          {progress['status'].upper()}")
    print(f"Total Tickets:   {progress['total_tickets']}")
    print(f"Completed:       {progress['completed_tickets']}")
    print(f"Failed:          {progress['failed_tickets']}")
    print(f"Remaining:       {progress['remaining_tickets']}")
    print(f"Progress:        {progress['progress_percentage']:.1f}%")
    
    if progress['current_ticket']:
        print(f"Current Ticket:  {progress['current_ticket']}")


def demo_basic_execution(db_session):
    """Demo 1: Basic sprint execution with completion."""
    print_section("Demo 1: Basic Sprint Execution")
    
    print("Starting a sprint with 5 tickets...")
    
    # Create orchestrator with custom execute_ticket
    orch = Orchestrator("SDT1", db=db_session, verbose=True)
    
    # Mock ticket execution
    executed_tickets = []
    original_execute = orch.execute_ticket
    
    def mock_execute_ticket(ticket_key):
        executed_tickets.append(ticket_key)
        time.sleep(0.1)  # Simulate work
        return True
    
    orch.execute_ticket = mock_execute_ticket
    
    # Mock get_sprint_tickets
    def mock_get_tickets(sprint_id):
        return [
            {"key": "SDT1-1", "summary": "First ticket", "execution_order": 1},
            {"key": "SDT1-2", "summary": "Second ticket", "execution_order": 2},
            {"key": "SDT1-3", "summary": "Third ticket", "execution_order": 3},
            {"key": "SDT1-4", "summary": "Fourth ticket", "execution_order": 4},
            {"key": "SDT1-5", "summary": "Fifth ticket", "execution_order": 5},
        ]
    
    orch.get_sprint_tickets = mock_get_tickets
    
    # Start sprint
    state_id = orch.start_sprint(
        sprint_id=101,
        sprint_name="Demo Sprint 1",
    )
    
    print()
    print("✓ Sprint completed successfully!")
    print()
    print_state(orch.state_manager, state_id)
    
    return state_id


def demo_crash_recovery(db_session):
    """Demo 2: Crash during execution and recovery."""
    print_section("Demo 2: Crash Recovery")
    
    print("Starting a sprint that will 'crash' partway through...")
    
    # Create orchestrator
    orch = Orchestrator("SDT1", db=db_session, verbose=True)
    
    # Mock ticket execution that crashes after 3 tickets
    executed_count = {"count": 0}
    
    def mock_execute_with_crash(ticket_key):
        executed_count["count"] += 1
        time.sleep(0.1)
        
        if executed_count["count"] == 3:
            print()
            print("💥 CRASH! Simulating server crash...")
            print()
            raise KeyboardInterrupt("Simulated crash")
        
        return True
    
    orch.execute_ticket = mock_execute_with_crash
    
    # Mock get_sprint_tickets
    def mock_get_tickets(sprint_id):
        return [
            {"key": "SDT1-10", "summary": "Ticket 1", "execution_order": 1},
            {"key": "SDT1-11", "summary": "Ticket 2", "execution_order": 2},
            {"key": "SDT1-12", "summary": "Ticket 3", "execution_order": 3},
            {"key": "SDT1-13", "summary": "Ticket 4", "execution_order": 4},
            {"key": "SDT1-14", "summary": "Ticket 5", "execution_order": 5},
        ]
    
    orch.get_sprint_tickets = mock_get_tickets
    
    # Start sprint (will crash)
    state_id = None
    try:
        state_id = orch.start_sprint(
            sprint_id=102,
            sprint_name="Demo Sprint 2",
        )
    except KeyboardInterrupt:
        print("Caught crash exception")
    
    # Get the state from the database
    state = orch.state_manager.db.query(
        orch.state_manager.db.query(
            orch.state_manager.db.query.__self__.__class__
        ).__self__
    )
    
    # Find the state we just created
    from models import OrchestratorState
    state = db_session.query(OrchestratorState).filter(
        OrchestratorState.sprint_id == 102
    ).first()
    
    if state:
        state_id = state.id
        
        print("Checking state after crash...")
        print()
        print_state(orch.state_manager, state_id)
        
        # Mark as failed so we can resume
        orch.state_manager.fail_execution(
            state_id,
            "Simulated crash during execution"
        )
        
        print()
        print("State marked as FAILED - ready for resume")
        print()
        
        # Now demonstrate resume
        print("─" * 80)
        print("Resuming execution from last checkpoint...")
        print("─" * 80)
        print()
        
        # Create new orchestrator instance (simulating restart)
        orch2 = Orchestrator("SDT1", db=db_session, verbose=True)
        
        # Mock execution that succeeds this time
        def mock_execute_success(ticket_key):
            time.sleep(0.1)
            return True
        
        orch2.execute_ticket = mock_execute_success
        
        # Resume
        orch2.resume_sprint(state_id)
        
        print()
        print("✓ Sprint recovered and completed successfully!")
        print()
        print_state(orch2.state_manager, state_id)
        
        return state_id
    
    return None


def demo_ticket_failure(db_session):
    """Demo 3: Handling ticket failures."""
    print_section("Demo 3: Ticket Failure Handling")
    
    print("Starting a sprint where some tickets will fail...")
    
    # Create orchestrator
    orch = Orchestrator("SDT1", db=db_session, verbose=True)
    
    # Mock ticket execution where ticket 2 and 4 fail
    def mock_execute_with_failures(ticket_key):
        time.sleep(0.1)
        
        if ticket_key in ["SDT1-22", "SDT1-24"]:
            raise Exception(f"Simulated failure for {ticket_key}")
        
        return True
    
    orch.execute_ticket = mock_execute_with_failures
    
    # Mock get_sprint_tickets
    def mock_get_tickets(sprint_id):
        return [
            {"key": "SDT1-21", "summary": "Ticket 1", "execution_order": 1},
            {"key": "SDT1-22", "summary": "Ticket 2 (will fail)", "execution_order": 2},
            {"key": "SDT1-23", "summary": "Ticket 3", "execution_order": 3},
            {"key": "SDT1-24", "summary": "Ticket 4 (will fail)", "execution_order": 4},
            {"key": "SDT1-25", "summary": "Ticket 5", "execution_order": 5},
        ]
    
    orch.get_sprint_tickets = mock_get_tickets
    
    # Start sprint
    state_id = orch.start_sprint(
        sprint_id=103,
        sprint_name="Demo Sprint 3",
    )
    
    print()
    print("✓ Sprint completed with some failures")
    print()
    print_state(orch.state_manager, state_id)
    
    # Show failed tickets
    state = orch.state_manager.get_state(state_id)
    if state.failed_tickets:
        print()
        print("Failed Tickets:")
        for failure in state.failed_tickets:
            print(f"  ✗ {failure['ticket_key']}: {failure['error_message']}")
    
    return state_id


def demo_list_resumable(db_session):
    """Demo 4: Listing resumable sprints."""
    print_section("Demo 4: Listing Resumable Sprints")
    
    print("Creating multiple sprints in different states...")
    print()
    
    # Create orchestrator
    orch = Orchestrator("SDT1", db=db_session, verbose=False)
    
    # Create a paused sprint
    state1 = orch.state_manager.create_state(
        sprint_id=201,
        sprint_name="Paused Sprint",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-1", "SDT1-2", "SDT1-3"],
    )
    orch.state_manager.start_execution(state1.id)
    orch.state_manager.mark_ticket_completed(state1.id, "SDT1-1")
    orch.state_manager.pause_execution(state1.id, "Manual pause")
    
    # Create a failed sprint
    state2 = orch.state_manager.create_state(
        sprint_id=202,
        sprint_name="Failed Sprint",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-4", "SDT1-5"],
    )
    orch.state_manager.start_execution(state2.id)
    orch.state_manager.mark_ticket_completed(state2.id, "SDT1-4")
    orch.state_manager.fail_execution(state2.id, "Critical error")
    
    # Create a completed sprint
    state3 = orch.state_manager.create_state(
        sprint_id=203,
        sprint_name="Completed Sprint",
        jira_project_key="SDT1",
        ticket_queue=["SDT1-6"],
    )
    orch.state_manager.start_execution(state3.id)
    orch.state_manager.mark_ticket_completed(state3.id, "SDT1-6")
    orch.state_manager.complete_execution(state3.id)
    
    # List resumable
    resumable = orch.list_resumable()
    
    print(f"Found {len(resumable)} resumable sprint(s):")
    print()
    
    for sprint in resumable:
        print(f"  {sprint['status'].upper()}: {sprint['sprint_name']}")
        print(f"    State ID:   {sprint['state_id']}")
        print(f"    Sprint ID:  {sprint['sprint_id']}")
        print(f"    Completed:  {sprint['completed']} / {sprint['total_tickets']}")
        print(f"    Failed:     {sprint['failed']}")
        print(f"    Remaining:  {sprint['remaining']}")
        print()


def main():
    """Run all demos."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "     Orchestrator Crash Recovery Demo".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")
    
    # Setup
    db_session = setup_test_database()
    
    try:
        # Run demos
        demo_basic_execution(db_session)
        demo_crash_recovery(db_session)
        demo_ticket_failure(db_session)
        demo_list_resumable(db_session)
        
        # Summary
        print_section("Demo Complete")
        print("All demonstrations completed successfully!")
        print()
        print("Key Takeaways:")
        print("  ✓ State is persisted after each ticket completion")
        print("  ✓ Crashes can be recovered by resuming from last checkpoint")
        print("  ✓ Failed tickets are tracked but don't stop execution")
        print("  ✓ Multiple sprints can be managed and resumed")
        print()
        print("For more information, see:")
        print("  docs/orchestrator-state-persistence.md")
        print()
        
    finally:
        db_session.close()


if __name__ == "__main__":
    main()
