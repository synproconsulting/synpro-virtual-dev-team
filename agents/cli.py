#!/usr/bin/env python3
"""
agents/cli.py
═════════════
Command-line interface for orchestrator state management.

This CLI tool allows operators to:
- Start sprint execution
- Resume paused/failed sprints
- Check execution progress
- List resumable sprints
- Pause/cancel running sprints

Usage:
    python -m agents.cli start --sprint-id 123 --sprint-name "Sprint 42" --project SDT1
    python -m agents.cli resume --state-id <uuid> --project SDT1
    python -m agents.cli list-resumable
    python -m agents.cli progress --state-id <uuid>
    python -m agents.cli pause --state-id <uuid> --reason "Maintenance"
    python -m agents.cli cancel --state-id <uuid> --reason "Cancelled by PM"
"""

import argparse
import sys
import os
from uuid import UUID
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../uat/backend"))

from database import SessionLocal, init_database
from agents.orchestrator import Orchestrator, start_sprint_execution, resume_sprint_execution
from agents.orchestrator_state import StateManager


def start_sprint(args: argparse.Namespace) -> int:
    """Start sprint execution.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        print(f"Starting sprint {args.sprint_id}: {args.sprint_name}")
        print(f"Project: {args.project}")
        print()
        
        state_id = start_sprint_execution(
            sprint_id=args.sprint_id,
            sprint_name=args.sprint_name,
            jira_project_key=args.project,
            verbose=True,
        )
        
        print()
        print(f"✓ Sprint execution completed")
        print(f"State ID: {state_id}")
        print()
        print("To check progress or resume later, use:")
        print(f"  python -m agents.cli progress --state-id {state_id}")
        print(f"  python -m agents.cli resume --state-id {state_id} --project {args.project}")
        
        return 0
        
    except KeyboardInterrupt:
        print()
        print("⚠ Execution interrupted by user")
        return 130
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


def resume_sprint(args: argparse.Namespace) -> int:
    """Resume sprint execution.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        state_id = UUID(args.state_id)
    except ValueError:
        print(f"✗ Invalid state ID format: {args.state_id}", file=sys.stderr)
        return 1
    
    try:
        print(f"Resuming sprint execution")
        print(f"State ID: {state_id}")
        print(f"Project: {args.project}")
        print()
        
        resume_sprint_execution(
            state_id=state_id,
            jira_project_key=args.project,
            verbose=True,
        )
        
        print()
        print(f"✓ Sprint execution completed")
        
        return 0
        
    except KeyboardInterrupt:
        print()
        print("⚠ Execution interrupted by user")
        return 130
    except ValueError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


def list_resumable(args: argparse.Namespace) -> int:
    """List resumable sprints.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        with SessionLocal() as db:
            orchestrator = Orchestrator(
                jira_project_key="DUMMY",  # Not used for listing
                db=db,
                verbose=False,
            )
            
            resumable = orchestrator.list_resumable()
        
        if not resumable:
            print("No resumable sprints found.")
            return 0
        
        print(f"Found {len(resumable)} resumable sprint(s):")
        print()
        
        for sprint in resumable:
            print(f"State ID:     {sprint['state_id']}")
            print(f"Sprint:       #{sprint['sprint_id']} - {sprint['sprint_name']}")
            print(f"Status:       {sprint['status'].upper()}")
            print(f"Progress:     {sprint['completed']}/{sprint['total_tickets']} completed, "
                  f"{sprint['failed']} failed, {sprint['remaining']} remaining")
            print(f"Last updated: {sprint['last_updated']}")
            print()
        
        return 0
        
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


def show_progress(args: argparse.Namespace) -> int:
    """Show execution progress.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        state_id = UUID(args.state_id)
    except ValueError:
        print(f"✗ Invalid state ID format: {args.state_id}", file=sys.stderr)
        return 1
    
    try:
        with SessionLocal() as db:
            state_manager = StateManager(db=db)
            progress = state_manager.get_progress(state_id)
        
        print(f"Sprint Progress")
        print(f"{'=' * 60}")
        print(f"State ID:         {progress['state_id']}")
        print(f"Sprint:           #{progress['sprint_id']} - {progress['sprint_name']}")
        print(f"Status:           {progress['status'].upper()}")
        print(f"Progress:         {progress['progress_percentage']:.1f}%")
        print()
        print(f"Total tickets:    {progress['total_tickets']}")
        print(f"Completed:        {progress['completed_tickets']}")
        print(f"Failed:           {progress['failed_tickets']}")
        print(f"Remaining:        {progress['remaining_tickets']}")
        print()
        
        if progress['current_ticket']:
            print(f"Current ticket:   {progress['current_ticket']}")
        
        if progress['started_at']:
            print(f"Started at:       {progress['started_at']}")
        
        if progress['last_checkpoint']:
            print(f"Last checkpoint:  {progress['last_checkpoint']}")
        
        return 0
        
    except ValueError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


def pause_sprint(args: argparse.Namespace) -> int:
    """Pause sprint execution.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        state_id = UUID(args.state_id)
    except ValueError:
        print(f"✗ Invalid state ID format: {args.state_id}", file=sys.stderr)
        return 1
    
    try:
        with SessionLocal() as db:
            orchestrator = Orchestrator(
                jira_project_key="DUMMY",  # Not used for pause
                db=db,
                verbose=False,
            )
            
            orchestrator.pause(state_id, args.reason)
        
        print(f"✓ Sprint execution paused")
        print(f"State ID: {state_id}")
        if args.reason:
            print(f"Reason: {args.reason}")
        
        return 0
        
    except ValueError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


def cancel_sprint(args: argparse.Namespace) -> int:
    """Cancel sprint execution.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        state_id = UUID(args.state_id)
    except ValueError:
        print(f"✗ Invalid state ID format: {args.state_id}", file=sys.stderr)
        return 1
    
    try:
        with SessionLocal() as db:
            orchestrator = Orchestrator(
                jira_project_key="DUMMY",  # Not used for cancel
                db=db,
                verbose=False,
            )
            
            orchestrator.cancel(state_id, args.reason)
        
        print(f"✓ Sprint execution cancelled")
        print(f"State ID: {state_id}")
        if args.reason:
            print(f"Reason: {args.reason}")
        
        return 0
        
    except ValueError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main CLI entry point.
    
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="Orchestrator state management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    subparsers.required = True
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start sprint execution")
    start_parser.add_argument(
        "--sprint-id",
        type=int,
        required=True,
        help="Jira sprint ID",
    )
    start_parser.add_argument(
        "--sprint-name",
        type=str,
        required=True,
        help="Sprint name",
    )
    start_parser.add_argument(
        "--project",
        type=str,
        required=True,
        help="Jira project key (e.g., SDT1)",
    )
    start_parser.set_defaults(func=start_sprint)
    
    # Resume command
    resume_parser = subparsers.add_parser("resume", help="Resume sprint execution")
    resume_parser.add_argument(
        "--state-id",
        type=str,
        required=True,
        help="State ID (UUID) to resume",
    )
    resume_parser.add_argument(
        "--project",
        type=str,
        required=True,
        help="Jira project key (e.g., SDT1)",
    )
    resume_parser.set_defaults(func=resume_sprint)
    
    # List resumable command
    list_parser = subparsers.add_parser("list-resumable", help="List resumable sprints")
    list_parser.set_defaults(func=list_resumable)
    
    # Progress command
    progress_parser = subparsers.add_parser("progress", help="Show execution progress")
    progress_parser.add_argument(
        "--state-id",
        type=str,
        required=True,
        help="State ID (UUID)",
    )
    progress_parser.set_defaults(func=show_progress)
    
    # Pause command
    pause_parser = subparsers.add_parser("pause", help="Pause sprint execution")
    pause_parser.add_argument(
        "--state-id",
        type=str,
        required=True,
        help="State ID (UUID)",
    )
    pause_parser.add_argument(
        "--reason",
        type=str,
        help="Reason for pausing",
    )
    pause_parser.set_defaults(func=pause_sprint)
    
    # Cancel command
    cancel_parser = subparsers.add_parser("cancel", help="Cancel sprint execution")
    cancel_parser.add_argument(
        "--state-id",
        type=str,
        required=True,
        help="State ID (UUID)",
    )
    cancel_parser.add_argument(
        "--reason",
        type=str,
        help="Reason for cancellation",
    )
    cancel_parser.set_defaults(func=cancel_sprint)
    
    args = parser.parse_args()
    
    # Ensure database is initialized
    try:
        init_database()
    except Exception as e:
        print(f"✗ Database initialization error: {e}", file=sys.stderr)
        print("Make sure DATABASE_URL environment variable is set", file=sys.stderr)
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
