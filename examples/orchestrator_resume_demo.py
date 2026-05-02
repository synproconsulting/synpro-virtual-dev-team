#!/usr/bin/env python3
"""
orchestrator_resume_demo.py
═══════════════════════════
Demonstration of orchestrator state persistence and resume capability.

This script demonstrates:
1. Starting a sprint execution
2. Simulating a crash mid-execution
3. Resuming from the saved state
4. Monitoring progress
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


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_progress(state_manager: StateManager, state_id: UUID):
    """Print current progress."""
    progress = state_manager.get_progress(state_id)
    
    print(f"State ID: {progress['state_id']}")
    print(f"Sprint: {progress['sprint_name']} (ID: {progress['sprint_id']})")
    print(f"Status: {progress['status'].upper()}")
    print(f"\nProgress: {progress['progress_percentage']:.1f}%")
    print(f"  ✓ Completed: {progress['completed_tickets']}/{progress['total_tickets']}")
    print(f"  ✗ Failed: {progress['failed_tickets']}")
    print(f"  ⏳ Remaining: {progress['remaining_tickets']}")
    
    if progress['current_ticket']:
        print(f"\nCurrently executing: {progress['current_ticket']}")


def demo_crash_recovery():
    """Demonstrate crash recovery scenario."""
    
    print_section("ORCHESTRATOR CRASH RECOVERY DEMO")
    
    # Setup in-memory database for demo
    print("Setting up test database...")
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Sample ticket queue
    tickets = ["SDT1-1", "SDT1-2", "SDT1-3", "SDT1-4", "SDT1-5"]
    
    # ── Phase 1: Initial Execution ────────────────────────────────────────────────────
    
    print_section("Phase 1: Starting Sprint Execution")
    
    state_manager = StateManager(db=db)
    state = state_manager.create_state(
        sprint_id=42,
        sprint_name="Sprint 10 - Demo",
        jira_project_key="SDT1",
        ticket_queue=tickets,
    )
    
    print(f"Created state: {state.id}")
    print(f"Tickets to execute: {tickets}")
    
    # Start execution
    state_manager.start_execution(state.id)
    print("\nStarting execution...")
    
    # Simulate execution of first 2 tickets
    for i, ticket in enumerate(tickets[:2], 1):
        print(f"\n[{i}] Executing {ticket}...")
        time.sleep(0.3)  # Simulate work
        
        state_manager.checkpoint(state.id, current_ticket=ticket)
        state_manager.mark_ticket_completed(state.id, ticket)
        
        print(f"    ✓ Completed {ticket}")
    
    # Show progress before crash
    print("\n" + "-"*80)
    print("Progress before crash:")
    print("-"*80)
    print_progress(state_manager, state.id)
    
    # ── Phase 2: Simulated Crash ──────────────────────────────────────────────────────
    
    print_section("Phase 2: Simulating System Crash")
    
    print("💥 CRASH! System encountered an error while executing SDT1-3")
    print("Marking execution as failed...")
    
    # Mark as failed (this would happen automatically in real crash recovery)
    state_manager.fail_execution(
        state.id,
        "System crash during ticket execution: Connection lost",
    )
    
    # Show state after crash
    print("\n" + "-"*80)
    print("State after crash:")
    print("-"*80)
    print_progress(state_manager, state.id)
    
    crashed_state = state_manager.get_state(state.id)
    print(f"\nError message: {crashed_state.error_message}")
    print(f"Completed tickets: {crashed_state.completed_tickets}")
    print(f"Remaining queue: {crashed_state.ticket_queue}")
    
    # ── Phase 3: System Recovery ──────────────────────────────────────────────────────
    
    print_section("Phase 3: System Recovery - Listing Resumable States")
    
    print("System has restarted. Checking for resumable executions...")
    
    resumable = state_manager.get_resumable_states()
    print(f"\nFound {len(resumable)} resumable state(s):")
    
    for rs in resumable:
        print(f"\n  State ID: {rs.id}")
        print(f"  Sprint: {rs.sprint_name} (ID: {rs.sprint_id})")
        print(f"  Status: {rs.status.value}")
        print(f"  Progress: {len(rs.completed_tickets or [])}/{rs.total_tickets} completed")
        print(f"  Remaining: {len(rs.ticket_queue or [])} tickets")
    
    # ── Phase 4: Resume Execution ─────────────────────────────────────────────────────
    
    print_section("Phase 4: Resuming Execution")
    
    print(f"Resuming state {state.id}...\n")
    
    # Resume execution
    state_manager.start_execution(state.id)
    
    # Get remaining tickets
    current_state = state_manager.get_state(state.id)
    remaining_tickets = current_state.ticket_queue.copy()
    
    print(f"Resuming with {len(remaining_tickets)} remaining tickets: {remaining_tickets}")
    
    # Execute remaining tickets
    for i, ticket in enumerate(remaining_tickets, len(current_state.completed_tickets) + 1):
        print(f"\n[{i}] Executing {ticket}...")
        time.sleep(0.3)  # Simulate work
        
        state_manager.checkpoint(state.id, current_ticket=ticket)
        state_manager.mark_ticket_completed(state.id, ticket)
        
        print(f"    ✓ Completed {ticket}")
    
    # Mark as completed
    state_manager.complete_execution(state.id)
    
    # ── Phase 5: Final Results ────────────────────────────────────────────────────────
    
    print_section("Phase 5: Execution Complete")
    
    print_progress(state_manager, state.id)
    
    final_state = state_manager.get_state(state.id)
    
    print("\nFinal Statistics:")
    print(f"  Total tickets: {final_state.total_tickets}")
    print(f"  ✓ Completed: {len(final_state.completed_tickets)}")
    print(f"  ✗ Failed: {len(final_state.failed_tickets)}")
    print(f"  Status: {final_state.status.value}")
    
    print(f"\nCompleted tickets: {final_state.completed_tickets}")
    
    if final_state.failed_tickets:
        print(f"\nFailed tickets:")
        for failure in final_state.failed_tickets:
            print(f"  - {failure['ticket_key']}: {failure['error_message']}")
    
    print_section("DEMO COMPLETE")
    
    print("Key Takeaways:")
    print("  1. ✓ State was persisted to database after each ticket")
    print("  2. ✓ After crash, execution state was preserved")
    print("  3. ✓ Resume picked up from last checkpoint")
    print("  4. ✓ Completed tickets were not re-executed")
    print("  5. ✓ All ticket history was maintained")
    
    print("\nThis demonstrates resilient sprint execution with automatic crash recovery!\n")
    
    # Cleanup
    db.close()


def demo_manual_pause_resume():
    """Demonstrate manual pause and resume."""
    
    print_section("MANUAL PAUSE AND RESUME DEMO")
    
    # Setup database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    tickets = ["SDT1-10", "SDT1-11", "SDT1-12"]
    
    # Create and start execution
    state_manager = StateManager(db=db)
    state = state_manager.create_state(
        sprint_id=43,
        sprint_name="Sprint 11 - Pause Demo",
        jira_project_key="SDT1",
        ticket_queue=tickets,
    )
    
    state_manager.start_execution(state.id)
    print(f"Started execution of {len(tickets)} tickets")
    
    # Execute one ticket
    print(f"\nExecuting {tickets[0]}...")
    state_manager.checkpoint(state.id, current_ticket=tickets[0])
    state_manager.mark_ticket_completed(state.id, tickets[0])
    print(f"✓ Completed {tickets[0]}")
    
    # Manual pause
    print("\n🛑 User requested pause (e.g., for system maintenance)")
    state_manager.pause_execution(state.id, "Manual pause for scheduled maintenance")
    
    print("\nExecution paused. Current state:")
    print_progress(state_manager, state.id)
    
    # Simulate some time passing
    print("\n⏳ System maintenance in progress...")
    time.sleep(1)
    
    # Resume
    print("\n▶️  Resuming execution after maintenance")
    state_manager.start_execution(state.id)
    
    # Complete remaining tickets
    current_state = state_manager.get_state(state.id)
    for ticket in current_state.ticket_queue.copy():
        print(f"\nExecuting {ticket}...")
        state_manager.checkpoint(state.id, current_ticket=ticket)
        state_manager.mark_ticket_completed(state.id, ticket)
        print(f"✓ Completed {ticket}")
    
    state_manager.complete_execution(state.id)
    
    print("\n" + "-"*80)
    print("Final state:")
    print("-"*80)
    print_progress(state_manager, state.id)
    
    print("\n✓ Pause and resume completed successfully!\n")
    
    db.close()


def main():
    """Run all demos."""
    try:
        # Demo 1: Crash recovery
        demo_crash_recovery()
        
        # Wait a bit between demos
        input("\nPress Enter to continue to Manual Pause/Resume demo...")
        
        # Demo 2: Manual pause and resume
        demo_manual_pause_resume()
        
        print("\n" + "="*80)
        print("  ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
