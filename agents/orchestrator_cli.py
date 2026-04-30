#!/usr/bin/env python3
"""
agents/orchestrator_cli.py
──────────────────────────
Command-line interface for managing orchestrator executions.

Usage examples:
    # Start a sprint
    python orchestrator_cli.py start --sprint-id 123 --sprint-name "Sprint 1" --project SDT1
    
    # Resume a paused sprint
    python orchestrator_cli.py resume --state-id <uuid>
    
    # List resumable sprints
    python orchestrator_cli.py list
    
    # Check progress
    python orchestrator_cli.py progress --state-id <uuid>
    
    # Pause execution
    python orchestrator_cli.py pause --state-id <uuid>
    
    # Cancel execution
    python orchestrator_cli.py cancel --state-id <uuid>
"""

import argparse
import sys
from uuid import UUID
from typing import Optional

from orchestrator import Orchestrator
from orchestrator_state import StateManager


def start_sprint(
    sprint_id: int,
    sprint_name: str,
    project_key: str,
    verbose: bool = True,
) -> None:
    """Start executing a sprint."""
    print(f"Starting sprint: {sprint_name} (ID: {sprint_id})")
    
    with Orchestrator(project_key, verbose=verbose) as orch:
        try:
            state_id = orch.start_sprint(sprint_id, sprint_name)
            print(f"\n✓ Sprint execution started")
            print(f"State ID: {state_id}")
            print(f"\nUse this state ID to resume, check progress, or manage execution.")
        except Exception as e:
            print(f"\n✗ Error starting sprint: {e}")
            sys.exit(1)


def resume_sprint(
    state_id: UUID,
    project_key: str,
    verbose: bool = True,
) -> None:
    """Resume a paused or failed sprint."""
    print(f"Resuming sprint from state: {state_id}")
    
    with Orchestrator(project_key, verbose=verbose) as orch:
        try:
            orch.resume_sprint(state_id)
            print(f"\n✓ Sprint execution resumed and completed")
        except ValueError as e:
            print(f"\n✗ Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"\n✗ Error resuming sprint: {e}")
            sys.exit(1)


def list_resumable(project_key: str) -> None:
    """List all resumable sprint executions."""
    with Orchestrator(project_key, verbose=False) as orch:
        resumable = orch.list_resumable()
        
        if not resumable:
            print("No resumable sprint executions found.")
            return
        
        print(f"\nResumable Sprint Executions:")
        print("=" * 80)
        
        for item in resumable:
            print(f"\nState ID: {item['state_id']}")
            print(f"  Sprint: {item['sprint_name']} (ID: {item['sprint_id']})")
            print(f"  Status: {item['status']}")
            print(f"  Progress: {item['completed']}/{item['total_tickets']} completed, "
                  f"{item['failed']} failed, {item['remaining']} remaining")
            print(f"  Last updated: {item['last_updated']}")


def show_progress(state_id: UUID, project_key: str) -> None:
    """Show execution progress for a sprint."""
    with Orchestrator(project_key, verbose=False) as orch:
        try:
            progress = orch.get_progress(state_id)
            
            print(f"\nSprint Execution Progress:")
            print("=" * 80)
            print(f"State ID: {progress['state_id']}")
            print(f"Sprint: {progress['sprint_name']} (ID: {progress['sprint_id']})")
            print(f"Status: {progress['status']}")
            print(f"\nProgress:")
            print(f"  Total tickets: {progress['total_tickets']}")
            print(f"  Completed: {progress['completed_tickets']}")
            print(f"  Failed: {progress['failed_tickets']}")
            print(f"  Remaining: {progress['remaining_tickets']}")
            print(f"  Current: {progress['current_ticket'] or 'None'}")
            print(f"  Progress: {progress['progress_percentage']}%")
            
            if progress['started_at']:
                print(f"\nStarted: {progress['started_at']}")
            if progress['last_checkpoint']:
                print(f"Last checkpoint: {progress['last_checkpoint']}")
                
        except ValueError as e:
            print(f"\n✗ Error: {e}")
            sys.exit(1)


def pause_sprint(state_id: UUID, project_key: str, reason: Optional[str] = None) -> None:
    """Pause a running sprint execution."""
    with Orchestrator(project_key, verbose=False) as orch:
        try:
            orch.pause(state_id, reason)
            print(f"✓ Sprint execution paused (State ID: {state_id})")
        except ValueError as e:
            print(f"✗ Error: {e}")
            sys.exit(1)


def cancel_sprint(state_id: UUID, project_key: str, reason: Optional[str] = None) -> None:
    """Cancel a sprint execution."""
    confirm = input(f"Are you sure you want to cancel execution {state_id}? (yes/no): ")
    if confirm.lower() != "yes":
        print("Cancelled.")
        return
    
    with Orchestrator(project_key, verbose=False) as orch:
        try:
            orch.cancel(state_id, reason)
            print(f"✓ Sprint execution cancelled (State ID: {state_id})")
        except ValueError as e:
            print(f"✗ Error: {e}")
            sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Orchestrator CLI - Manage sprint executions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start a sprint execution")
    start_parser.add_argument("--sprint-id", type=int, required=True, help="Jira sprint ID")
    start_parser.add_argument("--sprint-name", type=str, required=True, help="Sprint name")
    start_parser.add_argument("--project", type=str, required=True, help="Jira project key")
    start_parser.add_argument("--quiet", action="store_true", help="Quiet mode")
    
    # Resume command
    resume_parser = subparsers.add_parser("resume", help="Resume a paused sprint")
    resume_parser.add_argument("--state-id", type=str, required=True, help="State UUID")
    resume_parser.add_argument("--project", type=str, required=True, help="Jira project key")
    resume_parser.add_argument("--quiet", action="store_true", help="Quiet mode")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List resumable sprints")
    list_parser.add_argument("--project", type=str, required=True, help="Jira project key")
    
    # Progress command
    progress_parser = subparsers.add_parser("progress", help="Show execution progress")
    progress_parser.add_argument("--state-id", type=str, required=True, help="State UUID")
    progress_parser.add_argument("--project", type=str, required=True, help="Jira project key")
    
    # Pause command
    pause_parser = subparsers.add_parser("pause", help="Pause a running execution")
    pause_parser.add_argument("--state-id", type=str, required=True, help="State UUID")
    pause_parser.add_argument("--project", type=str, required=True, help="Jira project key")
    pause_parser.add_argument("--reason", type=str, help="Reason for pausing")
    
    # Cancel command
    cancel_parser = subparsers.add_parser("cancel", help="Cancel an execution")
    cancel_parser.add_argument("--state-id", type=str, required=True, help="State UUID")
    cancel_parser.add_argument("--project", type=str, required=True, help="Jira project key")
    cancel_parser.add_argument("--reason", type=str, help="Reason for cancellation")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == "start":
            start_sprint(
                args.sprint_id,
                args.sprint_name,
                args.project,
                verbose=not args.quiet,
            )
        
        elif args.command == "resume":
            state_id = UUID(args.state_id)
            resume_sprint(state_id, args.project, verbose=not args.quiet)
        
        elif args.command == "list":
            list_resumable(args.project)
        
        elif args.command == "progress":
            state_id = UUID(args.state_id)
            show_progress(state_id, args.project)
        
        elif args.command == "pause":
            state_id = UUID(args.state_id)
            pause_sprint(state_id, args.project, args.reason)
        
        elif args.command == "cancel":
            state_id = UUID(args.state_id)
            cancel_sprint(state_id, args.project, args.reason)
    
    except ValueError as e:
        print(f"✗ Invalid state ID: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
