"""
test_orchestrator_config.py
────────────────────────────
Tests for the Orchestrator configuration module.

Verifies that configuration constants are set correctly,
particularly the CI timeout extension from 15 to 30 minutes (SDT1-64).
"""

import os
import sys
import pytest

# Add agents directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../agents"))

from orchestrator_config import (
    CI_WAIT_TIMEOUT_MINUTES,
    CI_POLL_INTERVAL_SECONDS,
    CI_MAX_RETRIES,
    CI_RETRY_DELAY_SECONDS,
    MAX_CONCURRENT_TICKETS,
    CHECKPOINT_INTERVAL,
    FAILURE_STRATEGY,
    JIRA_EXECUTION_ORDER_FIELD,
    JIRA_STORY_POINTS_FIELD,
    JIRA_API_TIMEOUT,
    JIRA_API_MAX_RETRIES,
    STATE_RETENTION_DAYS,
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
    DB_POOL_TIMEOUT,
    LOG_LEVEL,
    LOG_FORMAT,
    DEFAULT_VERBOSE,
    get_ci_timeout_minutes,
    get_ci_poll_interval_seconds,
    get_jira_execution_order_field,
    get_jira_story_points_field,
    print_config,
)


class TestCIConfiguration:
    """Test CI/CD monitoring configuration."""
    
    def test_ci_timeout_is_30_minutes(self):
        """Verify CI timeout is 30 minutes (SDT1-64)."""
        assert CI_WAIT_TIMEOUT_MINUTES == 30
    
    def test_ci_timeout_getter(self):
        """Test CI timeout getter function."""
        assert get_ci_timeout_minutes() == 30
    
    def test_ci_poll_interval_is_30_seconds(self):
        """Verify CI poll interval is 30 seconds."""
        assert CI_POLL_INTERVAL_SECONDS == 30
    
    def test_ci_poll_interval_getter(self):
        """Test CI poll interval getter function."""
        assert get_ci_poll_interval_seconds() == 30
    
    def test_ci_max_retries(self):
        """Verify CI max retries is configured."""
        assert CI_MAX_RETRIES == 3
        assert isinstance(CI_MAX_RETRIES, int)
    
    def test_ci_retry_delay(self):
        """Verify CI retry delay is configured."""
        assert CI_RETRY_DELAY_SECONDS == 60
        assert isinstance(CI_RETRY_DELAY_SECONDS, int)


class TestOrchestratorConfiguration:
    """Test orchestrator execution configuration."""
    
    def test_max_concurrent_tickets(self):
        """Verify max concurrent tickets configuration."""
        assert MAX_CONCURRENT_TICKETS == 1
        assert isinstance(MAX_CONCURRENT_TICKETS, int)
    
    def test_checkpoint_interval(self):
        """Verify checkpoint interval configuration."""
        assert CHECKPOINT_INTERVAL == 1
        assert isinstance(CHECKPOINT_INTERVAL, int)
    
    def test_failure_strategy(self):
        """Verify failure strategy configuration."""
        assert FAILURE_STRATEGY in ["continue", "pause"]
        assert isinstance(FAILURE_STRATEGY, str)


class TestJiraConfiguration:
    """Test Jira integration configuration."""
    
    def test_execution_order_field(self):
        """Verify execution_order custom field ID."""
        assert JIRA_EXECUTION_ORDER_FIELD == "customfield_10071"
        assert isinstance(JIRA_EXECUTION_ORDER_FIELD, str)
    
    def test_execution_order_field_getter(self):
        """Test execution_order field getter function."""
        assert get_jira_execution_order_field() == "customfield_10071"
    
    def test_story_points_field(self):
        """Verify story_points custom field ID."""
        assert JIRA_STORY_POINTS_FIELD == "customfield_10016"
        assert isinstance(JIRA_STORY_POINTS_FIELD, str)
    
    def test_story_points_field_getter(self):
        """Test story_points field getter function."""
        assert get_jira_story_points_field() == "customfield_10016"
    
    def test_jira_api_timeout(self):
        """Verify Jira API timeout configuration."""
        assert JIRA_API_TIMEOUT == 30
        assert isinstance(JIRA_API_TIMEOUT, int)
    
    def test_jira_api_max_retries(self):
        """Verify Jira API max retries configuration."""
        assert JIRA_API_MAX_RETRIES == 3
        assert isinstance(JIRA_API_MAX_RETRIES, int)


class TestDatabaseConfiguration:
    """Test database configuration."""
    
    def test_state_retention_days(self):
        """Verify state retention period."""
        assert STATE_RETENTION_DAYS == 90
        assert isinstance(STATE_RETENTION_DAYS, int)
    
    def test_db_pool_size(self):
        """Verify database pool size."""
        assert DB_POOL_SIZE == 5
        assert isinstance(DB_POOL_SIZE, int)
    
    def test_db_max_overflow(self):
        """Verify database max overflow."""
        assert DB_MAX_OVERFLOW == 10
        assert isinstance(DB_MAX_OVERFLOW, int)
    
    def test_db_pool_timeout(self):
        """Verify database pool timeout."""
        assert DB_POOL_TIMEOUT == 30
        assert isinstance(DB_POOL_TIMEOUT, int)


class TestLoggingConfiguration:
    """Test logging configuration."""
    
    def test_log_level(self):
        """Verify log level configuration."""
        assert LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert isinstance(LOG_LEVEL, str)
    
    def test_log_format(self):
        """Verify log format is configured."""
        assert isinstance(LOG_FORMAT, str)
        assert "%(asctime)s" in LOG_FORMAT
        assert "%(levelname)s" in LOG_FORMAT
    
    def test_default_verbose(self):
        """Verify default verbose setting."""
        assert isinstance(DEFAULT_VERBOSE, bool)


class TestPrintConfig:
    """Test configuration printing function."""
    
    def test_print_config(self, capsys):
        """Test that print_config outputs configuration."""
        print_config()
        captured = capsys.readouterr()
        
        # Verify key sections are present
        assert "ORCHESTRATOR CONFIGURATION" in captured.out
        assert "CI/CD Monitoring:" in captured.out
        assert "30 minutes" in captured.out  # CI timeout
        assert "Execution:" in captured.out
        assert "Jira Integration:" in captured.out
        assert "Database:" in captured.out
        assert "Logging:" in captured.out
    
    def test_print_config_shows_timeout(self, capsys):
        """Test that print_config shows the 30-minute timeout."""
        print_config()
        captured = capsys.readouterr()
        
        assert "CI Wait Timeout:" in captured.out
        assert "30 minutes" in captured.out


class TestTimeoutIncrease:
    """Test suite specifically for SDT1-64 timeout increase."""
    
    def test_timeout_is_not_15_minutes(self):
        """Verify timeout is NOT the old value of 15 minutes."""
        assert CI_WAIT_TIMEOUT_MINUTES != 15
    
    def test_timeout_is_30_minutes(self):
        """Verify timeout IS the new value of 30 minutes."""
        assert CI_WAIT_TIMEOUT_MINUTES == 30
    
    def test_timeout_increased_by_100_percent(self):
        """Verify timeout doubled from 15 to 30 minutes."""
        old_timeout = 15
        new_timeout = CI_WAIT_TIMEOUT_MINUTES
        assert new_timeout == old_timeout * 2
    
    def test_timeout_allows_longer_pipelines(self):
        """Verify timeout is sufficient for complex CI pipelines."""
        # Typical pipeline stages and durations:
        unit_tests = 5  # minutes
        integration_tests = 10  # minutes
        e2e_tests = 15  # minutes
        deployment = 10  # minutes
        buffer = 5  # minutes for overhead
        
        total_expected = unit_tests + integration_tests + e2e_tests + deployment + buffer
        
        assert CI_WAIT_TIMEOUT_MINUTES >= total_expected
        assert CI_WAIT_TIMEOUT_MINUTES >= 30


class TestConfigurationConsistency:
    """Test that configuration values are consistent and reasonable."""
    
    def test_timeout_greater_than_poll_interval(self):
        """Verify timeout is significantly larger than poll interval."""
        timeout_seconds = CI_WAIT_TIMEOUT_MINUTES * 60
        assert timeout_seconds > CI_POLL_INTERVAL_SECONDS * 10
    
    def test_retry_delay_reasonable(self):
        """Verify retry delay is reasonable."""
        assert 30 <= CI_RETRY_DELAY_SECONDS <= 300  # Between 30s and 5min
    
    def test_max_retries_reasonable(self):
        """Verify max retries is reasonable."""
        assert 1 <= CI_MAX_RETRIES <= 10
    
    def test_pool_sizes_reasonable(self):
        """Verify database pool sizes are reasonable."""
        assert DB_POOL_SIZE > 0
        assert DB_MAX_OVERFLOW >= 0
        assert DB_POOL_TIMEOUT > 0
    
    def test_retention_period_reasonable(self):
        """Verify state retention period is reasonable."""
        assert STATE_RETENTION_DAYS >= 30  # At least 30 days
        assert STATE_RETENTION_DAYS <= 365  # At most 1 year
