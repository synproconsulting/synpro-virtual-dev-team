#!/usr/bin/env python3
"""
orchestrator_cli.py
══════════════════
Command-line interface for orchestrator state management.

Provides commands for:
- Starting sprint execution
- Resuming from saved state
- Listing resumable states
- Checking execution progress
- Pausing/canceling execution

Usage:
    python orchestrator_cli.py start --sprint-id 42 --sprint-name "Sprint 10" --project SDT1
    python orchestrator_cli.py resume --state-id <uuid>
    python orchestrator_cli.py list-resumable
    python orchestrator_cli.py progress --state-id <uuid>
    python orchestrator_cli.py pause --state-id <uuid>
    python orchestrator_cli.py cancel --state-id <uuid>
"""

import argparse
import sys
import os
from uuid import UUID
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../uat/backend"))

from orchestrator import Orchestrator, start_sprint_execution, resume_sprint_execution
from orchestrator_state import StateManager
from database import SessionLocal


def format_progress(progress: dict) -> str:
    """Format progress information for display.
    
    Args:
        progress: Progress dictionary from StateManager
        
    Returns:
        Formatted string for console output
    """
    lines = [
        f"\n{'='*80}",
        f"State ID: {progress['state_id']}",
        f"Sprint: {progress['sprint_name']} (ID: {progress['sprint_id']})",
        f"Status: {progress['status'].upper()}",
        f"{'='*80}",
        f"\nProgress: {progress['progress_percentage']:.1f}%",
        f"  Total tickets:     {progress['total_tickets']}",
        f"  ✓ Completed:       {progress['completed_tickets']}",
        f"  ✗ Failed:          {progress['failed_tickets']}",
        f"  ⏳ Remaining:       {progress['remaining_tickets']}",
    ]
    
    if progress['current_ticket']:
        lines.append(f"\nCurrently executing: {progress['current_ticket']}")
    
    if progress['started_at']:
        lines.append(f"\nStarted at: {progress['started_at']}")
    
    if progress['last_checkpoint']:
        lines.append(f"Last checkpoint: {progress['last_checkpoint']}")
    
    lines.append(f"{'='*80}\n")
    
    return "\n".join(lines)


def format_resumable_list(states: list) -> str:
    """Format list of resumable states for display.
    
    Args:
        states: List of state dictionaries
        
    Returns:
        Formatted string for console output
    """
    if not states:
        return "\nNo resumable states found.\n"
    
    lines = [
        f"\n{'='*80}",
        f"Resumable States ({len(states)} found)",
        f"{'='*80}\n",
    ]
    
    for state in states:
        lines.extend([
            f"State ID: {state['state_id']}",
            f"  Sprint: {state['sprint_name']} (ID: {state['sprint_id']})",
            f"  Status: {state['status'].upper()}",
            f"  Progress: {state['completed']}/{state['total_tickets']} completed, "
            f"{state['failed']} failed, {state['remaining']} remaining",
            f"  Last updated: {state['last_updated']}",
            "",
        ])
    
    lines.append(f"{'='*80}\n")
    
    return "\n".join(lines)


def cmd_start(args: argparse.Namespace) -> int:
    """Start a new sprint execution.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success)
    """
    print(f"Starting sprint execution...")
    print(f"  Sprint ID: {args.sprint_id}")
    print(f"  Sprint Name: {args.sprint_name}")
    print(f"  Project: {args.project}")
    
    try:
        state_id = start_sprint_execution(
            sprint_id=args.sprint_id,
            sprint_name=args.sprint_name,
            jira_project_key=args.project,
            verbose=True,
        )
        
        print(f"\n✓ Sprint execution started!")
        print(f"State ID: {state_id}")
        print(f"\nUse 'progress --state-id {state_id}' to check status.")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Failed to start sprint execution: {e}", file=sys.stderr)
        return 1


def cmd_resume(args: argparse.Namespace) -> int:
    """Resume a paused or failed sprint execution.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success)
    """
    try:
        state_id = UUID(args.state_id)
    except ValueError:
        print(f"✗ Invalid state ID: {args.state_id}", file=sys.stderr)
        return 1
    
    print(f"Resuming sprint execution...")
    print(f"  State ID: {state_id}")
    
    try:
        resume_sprint_execution(
            state_id=state_id,
            jira_project_key=args.project,
            verbose=True,
        )
        
        print(f"\n✓ Sprint execution completed!")
        print(f"\nUse 'progress --state-id {state_id}' to see final results.")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Failed to resume sprint execution: {e}", file=sys.stderr)
        return 1


def cmd_list_resumable(args: argparse.Namespace) -> int:
    """List all resumable sprint executions.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success)
    """
    try:
        with StateManager() as state_manager:
            states = state_manager.get_resumable_states()
            
            resumable_list = [
                {
                    "state_id": str(state.id),
                    "sprint_id": state.sprint_id,
                    "sprint_name": state.sprint_name,
                    "status": state.status.value,
                    "total_tickets": state.total_tickets,
                    "completed": len(state.completed_tickets or []),
                    "failed": len(state.failed_tickets or []),
                    "remaining": len(state.ticket_queue or []),
                    "last_updated": state.updated_at.isoformat(),
                }
                for state in states
            ]
            
            print(format_resumable_list(resumable_list))
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Failed to list resumable states: {e}", file=sys.stderr)
        return 1


def cmd_progress(args: argparse.Namespace) -> int:
    """Check progress of a sprint execution.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success)
    """
    try:
        state_id = UUID(args.state_id)
    except ValueError:
        print(f"✗ Invalid state ID: {args.state_id}", file=sys.stderr)
        return 1
    
    try:
        with StateManager() as state_manager:
            progress = state_manager.get_progress(state_id)
            print(format_progress(progress))
            
            # Show failed tickets if any
            state = state_manager.get_state(state_id)
            if state and state.failed_tickets:
                print("\nFailed Tickets:")
                print("-" * 80)
                for failure in state.failed_tickets:
                    print(f"  {failure['ticket_key']}: {failure['error_message']}")
                    print(f"    Timestamp: {failure['timestamp']}")
                    print()
        
        return 0
        
    except ValueError as e:
        print(f"\n✗ {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n✗ Failed to get progress: {e}", file=sys.stderr)
        return 1


def cmd_pause(args: argparse.Namespace) -> int:
    """Pause a running sprint execution.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success)
    """
    try:
        state_id = UUID(args.state_id)
    except ValueError:
        print(f"✗ Invalid state ID: {args.state_id}", file=sys.stderr)
        return 1
    
    try:
        with StateManager() as state_manager:
            state = state_manager.pause_execution(state_id, args.reason)
            print(f"\n✓ Sprint execution paused.")
            print(f"State ID: {state.id}")
            print(f"Status: {state.status.value}")
            
            if args.reason:
                print(f"Reason: {args.reason}")
        
        return 0
        
    except ValueError as e:
        print(f"\n✗ {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n✗ Failed to pause execution: {e}", file=sys.stderr)
        return 1


def cmd_cancel(args: argparse.Namespace) -> int:
    """Cancel a sprint execution.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success)
    """
    try:
        state_id = UUID(args.state_id)
    except ValueError:
        print(f"✗ Invalid state ID: {args.state_id}", file=sys.stderr)
        return 1
    
    # Confirm cancellation
    if not args.yes:
        response = input(f"Are you sure you want to cancel state {state_id}? [y/N] ")
        if response.lower() != 'y':
            print("Cancelled.")
            return 0
    
    try:
        with StateManager() as state_manager:
            state = state_manager.cancel_execution(state_id, args.reason)
            print(f"\n✓ Sprint execution cancelled.")
            print(f"State ID: {state.id}")
            print(f"Status: {state.status.value}")
            
            if args.reason:
                print(f"Reason: {args.reason}")
        
        return 0
        
    except ValueError as e:
        print(f"\n✗ {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n✗ Failed to cancel execution: {e}", file=sys.stderr)
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Orchestrator state management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start a new sprint execution")
    start_parser.add_argument("--sprint-id", type=int, required=True, help="Jira sprint ID")
    start_parser.add_argument("--sprint-name", type=str, required=True, help="Sprint name")
    start_parser.add_argument("--project", type=str, required=True, help="Jira project key")
    start_parser.set_defaults(func=cmd_start)
    
    # Resume command
    resume_parser = subparsers.add_parser("resume", help="Resume a paused or failed execution")
    resume_parser.add_argument("--state-id", type=str, required=True, help="State UUID to resume")
    resume_parser.add_argument("--project", type=str, required=True, help="Jira project key")
    resume_parser.set_defaults(func=cmd_resume)
    
    # List resumable command
    list_parser = subparsers.add_parser("list-resumable", help="List all resumable states")
    list_parser.set_defaults(func=cmd_list_resumable)
    
    # Progress command
    progress_parser = subparsers.add_parser("progress", help="Check execution progress")
    progress_parser.add_argument("--state-id", type=str, required=True, help="State UUID to check")
    progress_parser.set_defaults(func=cmd_progress)
    
    # Pause command
    pause_parser = subparsers.add_parser("pause", help="Pause a running execution")
    pause_parser.add_argument("--state-id", type=str, required=True, help="State UUID to pause")
    pause_parser.add_argument("--reason", type=str, help="Reason for pausing")
    pause_parser.set_defaults(func=cmd_pause)
    
    # Cancel command
    cancel_parser = subparsers.add_parser("cancel", help="Cancel an execution")
    cancel_parser.add_argument("--state-id", type=str, required=True, help="State UUID to cancel")
    cancel_parser.add_argument("--reason", type=str, help="Reason for cancellation")
    cancel_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    cancel_parser.set_defaults(func=cmd_cancel)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
