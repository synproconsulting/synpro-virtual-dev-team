"""
test_retrigger_loop_prevention.py
──────────────────────────────────
Integration tests for retrigger loop prevention.
These tests require GitHub API access (PAT_TOKEN) and should be run manually.

Usage:
    pytest tests/integration/test_retrigger_loop_prevention.py -v -s

Environment variables required:
    GITHUB_TOKEN or PAT_TOKEN
    GITHUB_USERNAME
    GITHUB_REPO
"""

import pytest
import os
import time
from unittest.mock import patch, Mock

# Skip all tests if running in CI without integration flag
pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_INTEGRATION_TESTS"),
    reason="Integration tests skipped. Set RUN_INTEGRATION_TESTS=1 to run."
)


@pytest.fixture
def github_env():
    """Ensure GitHub environment variables are set."""
    required = ["GITHUB_TOKEN", "GITHUB_USERNAME", "GITHUB_REPO"]
    missing = [var for var in required if not os.environ.get(var)]
    
    if missing:
        pytest.skip(f"Missing required environment variables: {missing}")
    
    return {
        "token": os.environ["GITHUB_TOKEN"],
        "username": os.environ["GITHUB_USERNAME"],
        "repo": os.environ["GITHUB_REPO"]
    }


class TestRetriggerLoopIntegration:
    """Integration tests using real GitHub API."""
    
    def test_count_retriggers_real_repo(self, github_env):
        """
        Test retrigger counting against real repository.
        This test is safe to run as it only reads data.
        """
        import ci_manager_agent as agent
        
        # Use a known test ticket or create a mock count
        # In a real scenario, you'd have test PRs set up
        count = agent.get_retrigger_count("SDT1-60")
        
        assert isinstance(count, int)
        assert count >= 0
        print(f"\nRetrigger count for SDT1-60: {count}")
    
    def test_retrigger_flow_simulation(self, github_env):
        """
        Simulate the retrigger flow without actually triggering workflows.
        This verifies the logic path without side effects.
        """
        import ci_manager_agent as agent
        
        with patch('ci_manager_agent.requests.post') as mock_post:
            # Mock successful dispatch
            mock_post.return_value.status_code = 204
            
            # Simulate first attempt (should succeed)
            with patch('ci_manager_agent.get_retrigger_count', return_value=0):
                result = agent.trigger_auto_implement(
                    "TEST-001",
                    "Test ticket",
                    "Test feedback",
                    pr_number=999
                )
                assert result is True
                print("\n✓ First attempt: triggered successfully")
            
            # Simulate second attempt (should succeed)
            with patch('ci_manager_agent.get_retrigger_count', return_value=1):
                result = agent.trigger_auto_implement(
                    "TEST-001",
                    "Test ticket",
                    "Test feedback",
                    pr_number=999
                )
                assert result is True
                print("✓ Second attempt: triggered successfully")
            
            # Simulate third attempt (should succeed)
            with patch('ci_manager_agent.get_retrigger_count', return_value=2):
                result = agent.trigger_auto_implement(
                    "TEST-001",
                    "Test ticket",
                    "Test feedback",
                    pr_number=999
                )
                assert result is True
                print("✓ Third attempt: triggered successfully")
            
            # Simulate fourth attempt (should be blocked)
            with patch('ci_manager_agent.get_retrigger_count', return_value=3):
                with patch('ci_manager_agent.post_comment') as mock_comment:
                    result = agent.trigger_auto_implement(
                        "TEST-001",
                        "Test ticket",
                        "Test feedback",
                        pr_number=999
                    )
                    assert result is False
                    assert mock_comment.called
                    print("✓ Fourth attempt: blocked by cap")


class TestRetriggerMessaging:
    """Test the messaging and notification system."""
    
    def test_cap_reached_message_format(self):
        """Verify cap reached message contains all required information."""
        import ci_manager_agent as agent
        
        with patch('ci_manager_agent.get_retrigger_count', return_value=3), \
             patch('ci_manager_agent.post_comment') as mock_comment, \
             patch('ci_manager_agent.jira_comment') as mock_jira:
            
            result = agent.trigger_auto_implement(
                "SDT1-60",
                "Test summary",
                "Test feedback",
                pr_number=123
            )
            
            assert result is False
            
            # Check PR comment
            pr_message = mock_comment.call_args[0][1]
            assert "Retrigger cap reached" in pr_message
            assert "3 attempts" in pr_message
            assert "Manual intervention" in pr_message
            assert "Possible causes:" in pr_message
            assert "Next steps:" in pr_message
            
            # Check Jira comment
            jira_message = mock_jira.call_args[0][1]
            assert "manual intervention" in jira_message.lower()
            assert "SDT1-60" in jira_message or "123" in jira_message
            
            print("\n✓ Messages contain all required information")
    
    def test_progress_message_format(self):
        """Verify progress messages show attempt counter."""
        import ci_manager_agent as agent
        
        for attempt in [0, 1, 2]:
            with patch('ci_manager_agent.get_retrigger_count', return_value=attempt), \
                 patch('ci_manager_agent.requests.post') as mock_post, \
                 patch('ci_manager_agent.post_comment') as mock_comment:
                
                mock_post.return_value.status_code = 204
                
                result = agent.trigger_auto_implement(
                    "SDT1-60",
                    "Test summary",
                    "Test feedback",
                    pr_number=123
                )
                
                assert result is True
                message = mock_comment.call_args[0][1]
                assert f"attempt {attempt + 1}/3" in message
                print(f"✓ Attempt {attempt + 1} message format correct")


class TestConfiguration:
    """Test configuration and environment variable handling."""
    
    def test_custom_max_attempts(self):
        """Test that custom MAX_RETRIGGER_ATTEMPTS is respected."""
        import ci_manager_agent as agent
        
        # Test with different cap values
        test_caps = [1, 2, 5, 10]
        
        for cap in test_caps:
            with patch.dict('os.environ', {'MAX_RETRIGGER_ATTEMPTS': str(cap)}):
                # Reload module to pick up new env var
                import importlib
                importlib.reload(agent)
                
                assert agent.MAX_RETRIGGER_ATTEMPTS == cap
                print(f"✓ Custom cap {cap} respected")


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_github_api_failure(self):
        """Test behavior when GitHub API is unavailable."""
        import ci_manager_agent as agent
        
        with patch('ci_manager_agent.requests.get') as mock_get:
            # Simulate API failure
            mock_get.side_effect = Exception("API unavailable")
            
            # Should return 0 and not crash
            count = agent.get_retrigger_count("SDT1-60")
            assert count == 0
            print("\n✓ Handles API failures gracefully")
    
    def test_malformed_pr_data(self):
        """Test handling of malformed PR data from API."""
        import ci_manager_agent as agent
        
        with patch('ci_manager_agent.requests.get') as mock_get:
            # Return malformed data
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = [
                {"invalid": "structure"},
                None,
                {"head": None, "title": None}
            ]
            
            # Should handle gracefully and return 0
            count = agent.get_retrigger_count("SDT1-60")
            assert count == 0
            print("\n✓ Handles malformed data gracefully")
    
    def test_workflow_dispatch_failure(self):
        """Test handling when workflow dispatch fails."""
        import ci_manager_agent as agent
        
        with patch('ci_manager_agent.get_retrigger_count', return_value=0), \
             patch('ci_manager_agent.requests.post') as mock_post, \
             patch('ci_manager_agent.post_comment') as mock_comment:
            
            # Simulate dispatch failure
            mock_post.return_value.status_code = 403
            mock_post.return_value.text = "Forbidden: Token lacks permissions"
            
            result = agent.trigger_auto_implement(
                "SDT1-60",
                "Test summary",
                "Test feedback",
                pr_number=123
            )
            
            assert result is False
            assert mock_comment.called
            message = mock_comment.call_args[0][1]
            assert "retrigger failed" in message
            assert "403" in message
            print("\n✓ Handles dispatch failures with clear messaging")


# Helper function to run integration tests manually
def run_integration_tests():
    """
    Helper to run integration tests with proper setup.
    
    Usage:
        RUN_INTEGRATION_TESTS=1 python -m pytest tests/integration/test_retrigger_loop_prevention.py -v -s
    """
    import subprocess
    import sys
    
    env = os.environ.copy()
    env["RUN_INTEGRATION_TESTS"] = "1"
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "-s"],
        env=env
    )
    
    return result.returncode


if __name__ == "__main__":
    # Allow running directly: python tests/integration/test_retrigger_loop_prevention.py
    exit(run_integration_tests())
