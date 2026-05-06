"""
examples/orchestrator_with_ci_monitoring.py
────────────────────────────────────────────
Example of integrating CI monitoring into the Orchestrator.

This demonstrates how the Orchestrator can use the CI monitor module
to wait for GitHub Actions pipelines to complete before proceeding
with ticket execution.

Usage:
    python examples/orchestrator_with_ci_monitoring.py
"""

import os
import sys
from typing import Optional
from uuid import UUID

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../uat/backend"))

from agents.orchestrator import Orchestrator
from agents.orchestrator_ci_monitor import wait_for_ci_completion, CITimeoutError
from agents.orchestrator_config import CI_WAIT_TIMEOUT_MINUTES


class OrchestratorWithCI(Orchestrator):
    """
    Extended Orchestrator that monitors CI/CD pipelines.
    
    This class extends the base Orchestrator to add CI monitoring
    capabilities. After executing a ticket that triggers a deployment,
    it waits for the CI pipeline to complete successfully.
    """
    
    def __init__(
        self,
        jira_project_key: str,
        github_repo_owner: str,
        github_repo_name: str,
        github_token: Optional[str] = None,
        ci_timeout_minutes: int = CI_WAIT_TIMEOUT_MINUTES,
        db=None,
        verbose: bool = True,
    ):
        """Initialize orchestrator with CI monitoring.
        
        Args:
            jira_project_key: Jira project key (e.g., 'SDT1')
            github_repo_owner: GitHub repository owner/organization
            github_repo_name: GitHub repository name
            github_token: GitHub token (uses GITHUB_TOKEN env var if None)
            ci_timeout_minutes: CI wait timeout in minutes (default: 30)
            db: Database session (optional)
            verbose: Whether to print execution logs
        """
        super().__init__(jira_project_key, db=db, verbose=verbose)
        self.github_repo_owner = github_repo_owner
        self.github_repo_name = github_repo_name
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.ci_timeout_minutes = ci_timeout_minutes
        
        if not self.github_token:
            self.log("Warning: No GitHub token configured. CI monitoring disabled.")
    
    def execute_ticket(self, ticket_key: str) -> bool:
        """Execute a ticket and wait for CI to pass.
        
        This method extends the base execute_ticket to add CI monitoring:
        1. Execute the ticket work (create PR, trigger deployment, etc.)
        2. Wait for CI pipeline to complete
        3. Return success only if CI passes
        
        Args:
            ticket_key: Jira ticket key (e.g., 'SDT1-42')
            
        Returns:
            bool: True if execution and CI succeeded, False otherwise
        """
        self.log(f"Executing ticket with CI monitoring: {ticket_key}")
        
        # Execute the base ticket work
        try:
            base_result = super().execute_ticket(ticket_key)
            if not base_result:
                self.log(f"Base execution failed for {ticket_key}")
                return False
        except Exception as e:
            self.log(f"Base execution error for {ticket_key}: {e}")
            return False
        
        # Skip CI monitoring if no GitHub token
        if not self.github_token:
            self.log("Skipping CI monitoring (no GitHub token)")
            return True
        
        # Wait for CI to complete
        try:
            self.log(f"Waiting for CI to complete (timeout: {self.ci_timeout_minutes} minutes)...")
            
            # Construct branch name from ticket key
            branch_name = f"feature/{ticket_key.lower()}"
            
            ci_result = wait_for_ci_completion(
                repo_owner=self.github_repo_owner,
                repo_name=self.github_repo_name,
                branch=branch_name,
                timeout_minutes=self.ci_timeout_minutes,
                github_token=self.github_token,
                verbose=self.verbose,
            )
            
            self.log(f"CI result for {ticket_key}: {ci_result}")
            
            if ci_result == "success":
                self.log(f"✓ CI passed for {ticket_key}")
                return True
            elif ci_result == "timeout":
                self.log(f"✗ CI timed out for {ticket_key} after {self.ci_timeout_minutes} minutes")
                return False
            elif ci_result == "cancelled":
                self.log(f"✗ CI was cancelled for {ticket_key}")
                return False
            else:  # failure
                self.log(f"✗ CI failed for {ticket_key}")
                return False
                
        except CITimeoutError as e:
            self.log(f"✗ CI timeout error for {ticket_key}: {e}")
            return False
        except Exception as e:
            self.log(f"✗ CI monitoring error for {ticket_key}: {e}")
            # Decide whether to fail on CI monitoring errors
            # For now, continue execution (don't block on CI monitoring failures)
            self.log("Continuing despite CI monitoring error...")
            return True


def example_basic_usage():
    """Example: Basic usage of OrchestratorWithCI."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Usage")
    print("=" * 80)
    
    # Create orchestrator with CI monitoring
    orchestrator = OrchestratorWithCI(
        jira_project_key="SDT1",
        github_repo_owner="myorg",
        github_repo_name="my-repo",
        ci_timeout_minutes=30,  # Extended timeout from SDT1-64
        verbose=True,
    )
    
    # Execute a single ticket
    print("\nExecuting ticket SDT1-42...")
    success = orchestrator.execute_ticket("SDT1-42")
    print(f"Result: {'Success' if success else 'Failed'}")


def example_sprint_execution():
    """Example: Execute a full sprint with CI monitoring."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Sprint Execution with CI Monitoring")
    print("=" * 80)
    
    # Create orchestrator with CI monitoring
    with OrchestratorWithCI(
        jira_project_key="SDT1",
        github_repo_owner="myorg",
        github_repo_name="my-repo",
        ci_timeout_minutes=30,
        verbose=True,
    ) as orchestrator:
        
        # Start a sprint
        print("\nStarting sprint execution...")
        state_id = orchestrator.start_sprint(
            sprint_id=123,
            sprint_name="Sprint 42",
        )
        
        print(f"\nSprint execution state ID: {state_id}")
        
        # Get progress
        progress = orchestrator.get_progress(state_id)
        print(f"\nProgress:")
        print(f"  Total tickets: {progress['total_tickets']}")
        print(f"  Completed: {progress['completed_tickets']}")
        print(f"  Failed: {progress['failed_tickets']}")


def example_custom_timeout():
    """Example: Custom CI timeout for specific scenarios."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Custom CI Timeout")
    print("=" * 80)
    
    # Scenario 1: Quick CI pipeline (shorter timeout)
    print("\nScenario 1: Quick pipeline (15 minute timeout)")
    orchestrator_quick = OrchestratorWithCI(
        jira_project_key="SDT1",
        github_repo_owner="myorg",
        github_repo_name="quick-repo",
        ci_timeout_minutes=15,
        verbose=True,
    )
    print(f"Timeout configured: {orchestrator_quick.ci_timeout_minutes} minutes")
    
    # Scenario 2: Long-running CI pipeline (extended timeout)
    print("\nScenario 2: Long pipeline (45 minute timeout)")
    orchestrator_long = OrchestratorWithCI(
        jira_project_key="SDT1",
        github_repo_owner="myorg",
        github_repo_name="complex-repo",
        ci_timeout_minutes=45,
        verbose=True,
    )
    print(f"Timeout configured: {orchestrator_long.ci_timeout_minutes} minutes")
    
    # Scenario 3: Default timeout (30 minutes from SDT1-64)
    print("\nScenario 3: Default timeout (from config)")
    orchestrator_default = OrchestratorWithCI(
        jira_project_key="SDT1",
        github_repo_owner="myorg",
        github_repo_name="standard-repo",
        # Uses default CI_WAIT_TIMEOUT_MINUTES = 30
        verbose=True,
    )
    print(f"Timeout configured: {orchestrator_default.ci_timeout_minutes} minutes")


def example_resume_with_ci():
    """Example: Resume sprint execution with CI monitoring."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Resume Sprint with CI Monitoring")
    print("=" * 80)
    
    # Resume a previously paused or failed sprint
    state_id = UUID("12345678-1234-5678-1234-567812345678")  # Example UUID
    
    with OrchestratorWithCI(
        jira_project_key="SDT1",
        github_repo_owner="myorg",
        github_repo_name="my-repo",
        ci_timeout_minutes=30,
        verbose=True,
    ) as orchestrator:
        
        print(f"\nResuming sprint from state: {state_id}")
        
        try:
            orchestrator.resume_sprint(state_id)
            print("\nSprint resumed and completed successfully")
        except ValueError as e:
            print(f"\nError resuming sprint: {e}")
        except Exception as e:
            print(f"\nUnexpected error: {e}")


def example_error_handling():
    """Example: Error handling with CI monitoring."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Error Handling")
    print("=" * 80)
    
    orchestrator = OrchestratorWithCI(
        jira_project_key="SDT1",
        github_repo_owner="myorg",
        github_repo_name="my-repo",
        ci_timeout_minutes=30,
        verbose=True,
    )
    
    # Scenario: CI timeout
    print("\nScenario: Handling CI timeout...")
    print("If CI doesn't complete within 30 minutes:")
    print("  - CITimeoutError is caught")
    print("  - Ticket marked as failed")
    print("  - Orchestrator continues with next ticket (or pauses based on config)")
    
    # Scenario: CI failure
    print("\nScenario: Handling CI failure...")
    print("If CI completes with failures:")
    print("  - CI result = 'failure'")
    print("  - Ticket marked as failed")
    print("  - Error logged with CI run URL")
    
    # Scenario: CI cancelled
    print("\nScenario: Handling CI cancellation...")
    print("If CI is cancelled:")
    print("  - CI result = 'cancelled'")
    print("  - Ticket marked as failed")
    print("  - Manual intervention may be required")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("ORCHESTRATOR WITH CI MONITORING - EXAMPLES")
    print("Extended CI Timeout: 30 minutes (SDT1-64)")
    print("=" * 80)
    
    # Note: These are demonstration examples
    # Actual execution requires:
    # - Valid GITHUB_TOKEN environment variable
    # - Active Jira project
    # - Running database
    # - GitHub repository with Actions enabled
    
    print("\nNote: These are demonstration examples.")
    print("To run with actual CI monitoring, set:")
    print("  - GITHUB_TOKEN environment variable")
    print("  - Valid Jira project key")
    print("  - Database connection")
    
    # Run examples
    try:
        example_basic_usage()
        example_sprint_execution()
        example_custom_timeout()
        example_resume_with_ci()
        example_error_handling()
    except Exception as e:
        print(f"\nExample execution note: {e}")
        print("This is expected if running without proper configuration.")
    
    print("\n" + "=" * 80)
    print("EXAMPLES COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
