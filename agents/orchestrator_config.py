"""
agents/orchestrator_config.py
──────────────────────────────
Configuration settings for the Orchestrator and related modules.

This module centralizes configuration constants to ensure consistency
across the orchestrator system.
"""

# ────────────────────────────────────────────────────────────────────────────
# CI/CD Monitoring Configuration
# ────────────────────────────────────────────────────────────────────────────

# CI wait timeout in minutes
# Extended from 15 to 30 minutes in SDT1-64 to accommodate longer CI pipelines
CI_WAIT_TIMEOUT_MINUTES = 30

# CI status poll interval in seconds
CI_POLL_INTERVAL_SECONDS = 30

# Maximum retries for transient CI monitoring errors
CI_MAX_RETRIES = 3

# Delay between retries in seconds
CI_RETRY_DELAY_SECONDS = 60


# ────────────────────────────────────────────────────────────────────────────
# Orchestrator Execution Configuration
# ────────────────────────────────────────────────────────────────────────────

# Maximum concurrent ticket executions (for future parallel execution)
MAX_CONCURRENT_TICKETS = 1

# Checkpoint interval (number of tickets between state checkpoints)
CHECKPOINT_INTERVAL = 1

# Failure handling strategy: "continue" or "pause"
FAILURE_STRATEGY = "continue"


# ────────────────────────────────────────────────────────────────────────────
# Jira Integration Configuration
# ────────────────────────────────────────────────────────────────────────────

# Jira custom field IDs
JIRA_EXECUTION_ORDER_FIELD = "customfield_10071"  # execution_order
JIRA_STORY_POINTS_FIELD = "customfield_10016"     # story_points

# Jira API timeouts (seconds)
JIRA_API_TIMEOUT = 30
JIRA_API_MAX_RETRIES = 3


# ────────────────────────────────────────────────────────────────────────────
# Database Configuration
# ────────────────────────────────────────────────────────────────────────────

# State retention period in days (for cleanup of old orchestrator states)
STATE_RETENTION_DAYS = 90

# Database connection pool settings
DB_POOL_SIZE = 5
DB_MAX_OVERFLOW = 10
DB_POOL_TIMEOUT = 30


# ────────────────────────────────────────────────────────────────────────────
# Logging Configuration
# ────────────────────────────────────────────────────────────────────────────

# Default log level for orchestrator
LOG_LEVEL = "INFO"

# Log format
LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"

# Enable verbose logging by default
DEFAULT_VERBOSE = True


# ────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ────────────────────────────────────────────────────────────────────────────

def get_ci_timeout_minutes() -> int:
    """Get configured CI wait timeout in minutes.
    
    Returns:
        int: CI wait timeout in minutes (default: 30)
    """
    return CI_WAIT_TIMEOUT_MINUTES


def get_ci_poll_interval_seconds() -> int:
    """Get configured CI poll interval in seconds.
    
    Returns:
        int: CI poll interval in seconds (default: 30)
    """
    return CI_POLL_INTERVAL_SECONDS


def get_jira_execution_order_field() -> str:
    """Get Jira custom field ID for execution_order.
    
    Returns:
        str: Custom field ID (customfield_10071)
    """
    return JIRA_EXECUTION_ORDER_FIELD


def get_jira_story_points_field() -> str:
    """Get Jira custom field ID for story_points.
    
    Returns:
        str: Custom field ID (customfield_10016)
    """
    return JIRA_STORY_POINTS_FIELD


# ────────────────────────────────────────────────────────────────────────────
# Configuration Summary
# ────────────────────────────────────────────────────────────────────────────

def print_config() -> None:
    """Print current orchestrator configuration."""
    print("=" * 80)
    print("ORCHESTRATOR CONFIGURATION")
    print("=" * 80)
    print(f"\nCI/CD Monitoring:")
    print(f"  CI Wait Timeout:        {CI_WAIT_TIMEOUT_MINUTES} minutes")
    print(f"  CI Poll Interval:       {CI_POLL_INTERVAL_SECONDS} seconds")
    print(f"  CI Max Retries:         {CI_MAX_RETRIES}")
    print(f"  CI Retry Delay:         {CI_RETRY_DELAY_SECONDS} seconds")
    print(f"\nExecution:")
    print(f"  Max Concurrent Tickets: {MAX_CONCURRENT_TICKETS}")
    print(f"  Checkpoint Interval:    {CHECKPOINT_INTERVAL}")
    print(f"  Failure Strategy:       {FAILURE_STRATEGY}")
    print(f"\nJira Integration:")
    print(f"  Execution Order Field:  {JIRA_EXECUTION_ORDER_FIELD}")
    print(f"  Story Points Field:     {JIRA_STORY_POINTS_FIELD}")
    print(f"  API Timeout:            {JIRA_API_TIMEOUT} seconds")
    print(f"  API Max Retries:        {JIRA_API_MAX_RETRIES}")
    print(f"\nDatabase:")
    print(f"  State Retention:        {STATE_RETENTION_DAYS} days")
    print(f"  Pool Size:              {DB_POOL_SIZE}")
    print(f"  Max Overflow:           {DB_MAX_OVERFLOW}")
    print(f"\nLogging:")
    print(f"  Log Level:              {LOG_LEVEL}")
    print(f"  Default Verbose:        {DEFAULT_VERBOSE}")
    print("=" * 80)


if __name__ == "__main__":
    # Print configuration when run directly
    print_config()
