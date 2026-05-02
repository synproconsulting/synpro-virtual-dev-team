#!/usr/bin/env python3
"""
agents/cli_orchestrator.py
──────────────────────────
Command-line interface for Sprint Orchestrator management.

This CLI tool allows operators to:
- Start sprint execution
- Resume interrupted sprints
- List resumable sprints
- Check execution progress
- Pause/cancel execution

Usage:
    python agents/cli_orchestrator.py start --sprint-id 123 --sprint-name "Sprint 1" --project SDT1
    python agents/cli_orchestrator.py resume --state-id <uuid> --project SDT1
    python agents/cli_orchestrator.py list-resumable --project SDT1
    python agents/cli_orchestrator.py progress --state-id <uuid> --project SDT1
    python agents/cli_orchestrator.py pause --state-id <uuid> --project SDT1
    python agents/cli_orchestrator.py cancel --state-id <uuid> --project SDT1
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
from models import OrchestratorStatus


def format_status(status: OrchestratorStatus) -> str:
    """Format status with color coding.
    
    Args:
        status: OrchestratorStatus enum value
        
    Returns:
        str: Formatted status string with color codes
    """
    colors = {
        OrchestratorStatus.PENDING: "\033[93m",      # Yellow
        OrchestratorStatus.RUNNING: "\033[94m",      # Blue
        OrchestratorStatus.PAUSED: "\033[93m",       # Yellow
        OrchestratorStatus.COMPLETED: "\033[92m",    # Green
        OrchestratorStatus.FAILED: "\033[91m",       # Red
        OrchestratorStatus.CANCELLED: "\033[90m",    # Gray
    }
    reset = "\033[0m"
    
    color = colors.get(status, "")
    return f"{color}{status.value.upper()}{reset}"


def cmd_start(args: argparse.Namespace) -> None:
    """Start a sprint execution.
    
    Args:
        args: Command-line arguments
    """
    print(f"Starting sprint execution:")
    print(f"  Sprint ID: {args.sprint_id}")
    print(f"  Sprint Name: {args.sprint_name}")
    print(f"  Project: {args.project}")
    print()
    
    try:
        state_id = start_sprint_execution(
            sprint_id=args.sprint_id,
            sprint_name=args.sprint_name,
            jira_project_key=args.project,
            verbose=args.verbose,
        )
        
        print(f"✓ Sprint execution started successfully")
        print(f"  State ID: {state_id}")
        print()
        print(f"Track progress with:")
        print(f"  python agents/cli_orchestrator.py progress --state-id {state_id} --project {args.project}")
        
    except Exception as e:
        print(f"✗ Failed to start sprint: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_resume(args: argparse.Namespace) -> None:
    """Resume a sprint execution.
    
    Args:
        args: Command-line arguments
    """
    try:
        state_id = UUID(args.state_id)
    except ValueError:
        print(f"✗ Invalid state ID format: {args.state_id}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Resuming sprint execution:")
    print(f"  State ID: {state_id}")
    print(f"  Project: {args.project}")
    print()
    
    try:
        resume_sprint_execution(
            state_id=state_id,
            jira_project_key=args.project,
            verbose=args.verbose,
        )
        
        print(f"✓ Sprint execution completed")
        
    except ValueError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Failed to resume sprint: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_list_resumable(args: argparse.Namespace) -> None:
    """List all resumable sprints.
    
    Args:
        args: Command-line arguments
    """
    try:
        with Orchestrator(args.project, verbose=False) as orch:
            resumable = orch.list_resumable()
            
            if not resumable:
                print("No resumable sprints found.")
                return
            
            print(f"Resumable sprints ({len(resumable)}):")
            print()
            
            for sprint in resumable:
                status = OrchestratorStatus(sprint["status"])
                print(f"  {format_status(status)} {sprint['sprint_name']}")
                print(f"    State ID:    {sprint['state_id']}")
                print(f"    Sprint ID:   {sprint['sprint_id']}")
                print(f"    Total:       {sprint['total_tickets']} tickets")
                print(f"    Completed:   {sprint['completed']}")
                print(f"    Failed:      {sprint['failed']}")
                print(f"    Remaining:   {sprint['remaining']}")
                print(f"    Last Update: {sprint['last_updated']}")
                print()
                print(f"    Resume with:")
                print(f"      python agents/cli_orchestrator.py resume --state-id {sprint['state_id']} --project {args.project}")
                print()
            
    except Exception as e:
        print(f"✗ Failed to list resumable sprints: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_progress(args: argparse.Namespace) -> None:
    """Check execution progress.
    
    Args:
        args: Command-line arguments
    """
    try:
        state_id = UUID(args.state_id)
    except ValueError:
        print(f"✗ Invalid state ID format: {args.state_id}", file=sys.stderr)
        sys.exit(1)
    
    try:
        with Orchestrator(args.project, verbose=False) as orch:
            progress = orch.get_progress(state_id)
            
            status = OrchestratorStatus(progress["status"])
            
            print(f"Sprint Execution Progress:")
            print()
            print(f"  Sprint:           {progress['sprint_name']} (ID: {progress['sprint_id']})")
            print(f"  State ID:         {progress['state_id']}")
            print(f"  Status:           {format_status(status)}")
            print()
            print(f"  Total Tickets:    {progress['total_tickets']}")
            print(f"  Completed:        {progress['completed_tickets']}")
            print(f"  Failed:           {progress['failed_tickets']}")
            print(f"  Remaining:        {progress['remaining_tickets']}")
            print(f"  Progress:         {progress['progress_percentage']:.1f}%")
            print()
            
            if progress['current_ticket']:
                print(f"  Current Ticket:   {progress['current_ticket']}")
                print()
            
            if progress['started_at']:
                print(f"  Started:          {progress['started_at']}")
            
            if progress['last_checkpoint']:
                print(f"  Last Checkpoint:  {progress['last_checkpoint']}")
            
            # Show progress bar
            bar_length = 40
            filled = int(bar_length * progress['progress_percentage'] / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            print()
            print(f"  [{bar}] {progress['progress_percentage']:.1f}%")
            
    except ValueError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Failed to get progress: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_pause(args: argparse.Namespace) -> None:
    """Pause a sprint execution.
    
    Args:
        args: Command-line arguments
    """
    try:
        state_id = UUID(args.state_id)
    except ValueError:
        print(f"✗ Invalid state ID format: {args.state_id}", file=sys.stderr)
        sys.exit(1)
    
    try:
        with Orchestrator(args.project, verbose=False) as orch:
            orch.pause(state_id, reason=args.reason)
            
            print(f"✓ Sprint execution paused")
            print(f"  State ID: {state_id}")
            if args.reason:
                print(f"  Reason: {args.reason}")
            print()
            print(f"Resume with:")
            print(f"  python agents/cli_orchestrator.py resume --state-id {state_id} --project {args.project}")
            
    except Exception as e:
        print(f"✗ Failed to pause sprint: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_cancel(args: argparse.Namespace) -> None:
    """Cancel a sprint execution.
    
    Args:
        args: Command-line arguments
    """
    try:
        state_id = UUID(args.state_id)
    except ValueError:
        print(f"✗ Invalid state ID format: {args.state_id}", file=sys.stderr)
        sys.exit(1)
    
    # Confirm cancellation
    if not args.force:
        print(f"⚠️  WARNING: Cancelling execution cannot be undone.")
        print(f"   State ID: {state_id}")
        response = input("   Are you sure? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("Cancelled by user.")
            return
    
    try:
        with Orchestrator(args.project, verbose=False) as orch:
            orch.cancel(state_id, reason=args.reason)
            
            print(f"✓ Sprint execution cancelled")
            print(f"  State ID: {state_id}")
            if args.reason:
                print(f"  Reason: {args.reason}")
            
    except Exception as e:
        print(f"✗ Failed to cancel sprint: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Sprint Orchestrator CLI - Manage sprint execution with resume capability",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    subparsers.required = True
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start a sprint execution")
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
    start_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    start_parser.set_defaults(func=cmd_start)
    
    # Resume command
    resume_parser = subparsers.add_parser("resume", help="Resume a sprint execution")
    resume_parser.add_argument(
        "--state-id",
        type=str,
        required=True,
        help="UUID of the orchestrator state",
    )
    resume_parser.add_argument(
        "--project",
        type=str,
        required=True,
        help="Jira project key",
    )
    resume_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    resume_parser.set_defaults(func=cmd_resume)
    
    # List resumable command
    list_parser = subparsers.add_parser(
        "list-resumable",
        help="List all resumable sprints",
    )
    list_parser.add_argument(
        "--project",
        type=str,
        required=True,
        help="Jira project key",
    )
    list_parser.set_defaults(func=cmd_list_resumable)
    
    # Progress command
    progress_parser = subparsers.add_parser(
        "progress",
        help="Check execution progress",
    )
    progress_parser.add_argument(
        "--state-id",
        type=str,
        required=True,
        help="UUID of the orchestrator state",
    )
    progress_parser.add_argument(
        "--project",
        type=str,
        required=True,
        help="Jira project key",
    )
    progress_parser.set_defaults(func=cmd_progress)
    
    # Pause command
    pause_parser = subparsers.add_parser("pause", help="Pause a sprint execution")
    pause_parser.add_argument(
        "--state-id",
        type=str,
        required=True,
        help="UUID of the orchestrator state",
    )
    pause_parser.add_argument(
        "--project",
        type=str,
        required=True,
        help="Jira project key",
    )
    pause_parser.add_argument(
        "--reason",
        type=str,
        help="Reason for pausing",
    )
    pause_parser.set_defaults(func=cmd_pause)
    
    # Cancel command
    cancel_parser = subparsers.add_parser("cancel", help="Cancel a sprint execution")
    cancel_parser.add_argument(
        "--state-id",
        type=str,
        required=True,
        help="UUID of the orchestrator state",
    )
    cancel_parser.add_argument(
        "--project",
        type=str,
        required=True,
        help="Jira project key",
    )
    cancel_parser.add_argument(
        "--reason",
        type=str,
        help="Reason for cancellation",
    )
    cancel_parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt",
    )
    cancel_parser.set_defaults(func=cmd_cancel)
    
    # Parse arguments and execute command
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
