#!/usr/bin/env python3
"""
tools/orchestrator_cli.py
─────────────────────────
Command-line interface for managing orchestrator executions.

Usage:
    python tools/orchestrator_cli.py start <sprint_id> <sprint_name> [--project PROJECT]
    python tools/orchestrator_cli.py resume <state_id> [--project PROJECT]
    python tools/orchestrator_cli.py status <state_id>
    python tools/orchestrator_cli.py list-resumable
    python tools/orchestrator_cli.py pause <state_id> [--reason REASON]
    python tools/orchestrator_cli.py cancel <state_id> [--reason REASON]

Examples:
    # Start a sprint execution
    python tools/orchestrator_cli.py start 123 "Sprint 10" --project SDT1
    
    # Resume after a crash
    python tools/orchestrator_cli.py resume a1b2c3d4-e5f6-7890-abcd-ef1234567890 --project SDT1
    
    # Check execution status
    python tools/orchestrator_cli.py status a1b2c3d4-e5f6-7890-abcd-ef1234567890
    
    # List all resumable states
    python tools/orchestrator_cli.py list-resumable
    
    # Pause an execution
    python tools/orchestrator_cli.py pause a1b2c3d4-e5f6-7890-abcd-ef1234567890 --reason "Manual pause"
"""

import argparse
import os
import sys
from pathlib import Path
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "uat" / "backend"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.orchestrator import Orchestrator
from agents.orchestrator_state import StateManager
from database import SessionLocal


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_success(message: str) -> None:
    """Print success message in green."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str) -> None:
    """Print error message in red."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}", file=sys.stderr)


def print_info(message: str) -> None:
    """Print info message in cyan."""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


def print_warning(message: str) -> None:
    """Print warning message in yellow."""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_header(message: str) -> None:
    """Print header message in bold."""
    print(f"\n{Colors.BOLD}{message}{Colors.ENDC}")


def start_sprint(args: argparse.Namespace) -> None:
    """Start a sprint execution."""
    print_header(f"Starting Sprint Execution")
    print_info(f"Sprint ID: {args.sprint_id}")
    print_info(f"Sprint Name: {args.sprint_name}")
    print_info(f"Project: {args.project}")
    
    try:
        with Orchestrator(jira_project_key=args.project, verbose=True) as orchestrator:
            state_id = orchestrator.start_sprint(
                sprint_id=args.sprint_id,
                sprint_name=args.sprint_name,
            )
            
            print_success(f"Sprint execution started!")
            print_info(f"State ID: {state_id}")
            print_info(f"Use 'status {state_id}' to check progress")
            print_info(f"Use 'resume {state_id}' to resume if interrupted")
            
    except Exception as e:
        print_error(f"Failed to start sprint: {e}")
        sys.exit(1)


def resume_sprint(args: argparse.Namespace) -> None:
    """Resume a sprint execution."""
    print_header(f"Resuming Sprint Execution")
    print_info(f"State ID: {args.state_id}")
    print_info(f"Project: {args.project}")
    
    try:
        state_id = UUID(args.state_id)
        
        with Orchestrator(jira_project_key=args.project, verbose=True) as orchestrator:
            orchestrator.resume_sprint(state_id)
            
            print_success(f"Sprint execution resumed successfully!")
            
    except ValueError as e:
        print_error(f"Invalid state ID or state cannot be resumed: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to resume sprint: {e}")
        sys.exit(1)


def show_status(args: argparse.Namespace) -> None:
    """Show execution status."""
    try:
        state_id = UUID(args.state_id)
        
        with StateManager() as state_manager:
            progress = state_manager.get_progress(state_id)
            
            print_header(f"Execution Status")
            print(f"State ID:           {progress['state_id']}")
            print(f"Sprint:             {progress['sprint_name']} (ID: {progress['sprint_id']})")
            print(f"Status:             {progress['status']}")
            print(f"Progress:           {progress['progress_percentage']:.1f}%")
            print(f"Total Tickets:      {progress['total_tickets']}")
            print(f"Completed:          {progress['completed_tickets']}")
            print(f"Failed:             {progress['failed_tickets']}")
            print(f"Remaining:          {progress['remaining_tickets']}")
            
            if progress['current_ticket']:
                print(f"Current Ticket:     {progress['current_ticket']}")
            
            if progress['started_at']:
                print(f"Started:            {progress['started_at']}")
            
            if progress['last_checkpoint']:
                print(f"Last Checkpoint:    {progress['last_checkpoint']}")
            
            # Get full state for failed tickets detail
            state = state_manager.get_state(state_id)
            if state and state.failed_tickets:
                print_header("Failed Tickets:")
                for failure in state.failed_tickets:
                    print(f"  • {failure['ticket_key']}: {failure['error_message']}")
                    print(f"    Time: {failure['timestamp']}")
            
    except ValueError:
        print_error("Invalid state ID format")
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to get status: {e}")
        sys.exit(1)


def list_resumable(args: argparse.Namespace) -> None:
    """List all resumable states."""
    try:
        with Orchestrator(jira_project_key="", verbose=False) as orchestrator:
            resumable = orchestrator.list_resumable()
            
            if not resumable:
                print_info("No resumable states found.")
                return
            
            print_header(f"Resumable States ({len(resumable)} found)")
            
            for state in resumable:
                print(f"\n{Colors.BOLD}State ID:{Colors.ENDC} {state['state_id']}")
                print(f"  Sprint:      {state['sprint_name']} (ID: {state['sprint_id']})")
                print(f"  Status:      {state['status']}")
                print(f"  Progress:    {state['completed']}/{state['total_tickets']} completed")
                print(f"  Failed:      {state['failed']}")
                print(f"  Remaining:   {state['remaining']}")
                print(f"  Last Update: {state['last_updated']}")
                
                if state['status'] == 'paused':
                    print_info(f"  → Use 'resume {state['state_id']}' to continue")
                elif state['status'] == 'failed':
                    print_warning(f"  → Use 'resume {state['state_id']}' to retry")
            
    except Exception as e:
        print_error(f"Failed to list resumable states: {e}")
        sys.exit(1)


def pause_execution(args: argparse.Namespace) -> None:
    """Pause an execution."""
    try:
        state_id = UUID(args.state_id)
        
        with StateManager() as state_manager:
            state_manager.pause_execution(state_id, reason=args.reason)
            
            print_success(f"Execution paused")
            print_info(f"State ID: {args.state_id}")
            if args.reason:
                print_info(f"Reason: {args.reason}")
            print_info(f"Use 'resume {args.state_id}' to continue")
            
    except ValueError as e:
        print_error(f"Invalid state ID or state not found: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to pause execution: {e}")
        sys.exit(1)


def cancel_execution(args: argparse.Namespace) -> None:
    """Cancel an execution."""
    try:
        state_id = UUID(args.state_id)
        
        with StateManager() as state_manager:
            state_manager.cancel_execution(state_id, reason=args.reason)
            
            print_success(f"Execution cancelled")
            print_info(f"State ID: {args.state_id}")
            if args.reason:
                print_info(f"Reason: {args.reason}")
            print_warning("Note: Cancelled executions cannot be resumed")
            
    except ValueError as e:
        print_error(f"Invalid state ID or state not found: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to cancel execution: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Orchestrator CLI - Manage sprint executions with state persistence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s start 123 "Sprint 10" --project SDT1
  %(prog)s resume a1b2c3d4-e5f6-7890-abcd-ef1234567890 --project SDT1
  %(prog)s status a1b2c3d4-e5f6-7890-abcd-ef1234567890
  %(prog)s list-resumable
  %(prog)s pause a1b2c3d4-e5f6-7890-abcd-ef1234567890 --reason "Manual pause"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    subparsers.required = True
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start a sprint execution")
    start_parser.add_argument("sprint_id", type=int, help="Jira sprint ID")
    start_parser.add_argument("sprint_name", help="Sprint name")
    start_parser.add_argument(
        "--project", "-p",
        default=os.getenv("JIRA_PROJECT_KEY", "SDT1"),
        help="Jira project key (default: SDT1 or JIRA_PROJECT_KEY env var)"
    )
    start_parser.set_defaults(func=start_sprint)
    
    # Resume command
    resume_parser = subparsers.add_parser("resume", help="Resume a sprint execution")
    resume_parser.add_argument("state_id", help="UUID of orchestrator state to resume")
    resume_parser.add_argument(
        "--project", "-p",
        default=os.getenv("JIRA_PROJECT_KEY", "SDT1"),
        help="Jira project key (default: SDT1 or JIRA_PROJECT_KEY env var)"
    )
    resume_parser.set_defaults(func=resume_sprint)
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show execution status")
    status_parser.add_argument("state_id", help="UUID of orchestrator state")
    status_parser.set_defaults(func=show_status)
    
    # List resumable command
    list_parser = subparsers.add_parser("list-resumable", help="List all resumable states")
    list_parser.set_defaults(func=list_resumable)
    
    # Pause command
    pause_parser = subparsers.add_parser("pause", help="Pause an execution")
    pause_parser.add_argument("state_id", help="UUID of orchestrator state")
    pause_parser.add_argument("--reason", "-r", help="Reason for pausing")
    pause_parser.set_defaults(func=pause_execution)
    
    # Cancel command
    cancel_parser = subparsers.add_parser("cancel", help="Cancel an execution")
    cancel_parser.add_argument("state_id", help="UUID of orchestrator state")
    cancel_parser.add_argument("--reason", "-r", help="Reason for cancellation")
    cancel_parser.set_defaults(func=cancel_execution)
    
    args = parser.parse_args()
    
    # Check for DATABASE_URL
    if not os.getenv("DATABASE_URL"):
        print_error("DATABASE_URL environment variable not set")
        print_info("Please set DATABASE_URL to connect to the database")
        sys.exit(1)
    
    # Execute the command
    args.func(args)


if __name__ == "__main__":
    main()
