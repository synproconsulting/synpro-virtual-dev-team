"""
Tests for Manager Agent with exponential backoff retry logic and diff review.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import httpx

from manager_agent import (
    JiraRetryClient,
    ManagerAgent,
    RetriggerTracker,
    RetriggerAttempt,
    TransitionStatus,
    TransitionResult,
    DiffReviewResult,
    create_manager_agent,
    DEFAULT_MAX_RETRIES,
    DEFAULT_BASE_DELAY,
    DEFAULT_MAX_RETRIGGERS,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("JIRA_BASE_URL", "https://test.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "test@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
    monkeypatch.setenv("JIRA_PROJECT_KEY", "TEST")


@pytest.fixture
def retry_client(mock_env):
    """Create a JiraRetryClient for testing."""
    return JiraRetryClient(max_retries=3, base_delay=0.1)


@pytest.fixture
def manager_agent(mock_env):
    """Create a ManagerAgent for testing."""
    return ManagerAgent(max_retries=3, base_delay=0.1)


@pytest.fixture
def retrigger_tracker():
    """Create a RetriggerTracker for testing."""
    return RetriggerTracker(max_retriggers=3, window_seconds=60, cooldown_seconds=30)


# Sample diffs for testing
SAMPLE_NEW_FILE_DIFF = """diff --git a/tools/new_feature.py b/tools/new_feature.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/tools/new_feature.py
@@ -0,0 +1,10 @@
+def new_function():
+    return "Hello"
"""

SAMPLE_MODIFIED_FILE_DIFF = """diff --git a/tools/existing.py b/tools/existing.py
index abcdef1..1234567 100644
--- a/tools/existing.py
+++ b/tools/existing.py
@@ -1,5 +1,8 @@
 def existing_function():
-    return "old"
+    return "new"
"""


# ── Retrigger Tracker Tests ───────────────────────────────────────────────────────────


class TestRetriggerTracker:
    """Test RetriggerTracker functionality."""
    
    def test_initial_state(self, retrigger_tracker):
        """Test tracker initial state."""
        can_retrigger, reason = retrigger_tracker.can_retrigger("TEST-1", "start_work")
        assert can_retrigger is True
        assert reason is None
        
        count = retrigger_tracker.get_retrigger_count("TEST-1", "start_work")
        assert count == 0
    
    def test_record_single_retrigger(self, retrigger_tracker):
        """Test recording a single retrigger."""
        count = retrigger_tracker.record_retrigger("TEST-1", "start_work", "success")
        assert count == 1
        
        # Should still be able to retrigger
        can_retrigger, reason = retrigger_tracker.can_retrigger("TEST-1", "start_work")
        assert can_retrigger is True
    
    def test_max_retriggers_exceeded(self, retrigger_tracker):
        """Test that max retriggers limit is enforced."""
        # Record max_retriggers (3) attempts
        for i in range(3):
            retrigger_tracker.record_retrigger("TEST-1", "start_work", "attempt")
        
        # Next attempt should be blocked
        can_retrigger, reason = retrigger_tracker.can_retrigger("TEST-1", "start_work")
        assert can_retrigger is False
        assert "Maximum retrigger limit" in reason
        assert "TEST-1" in reason
    
    def test_different_operations_tracked_separately(self, retrigger_tracker):
        """Test that different operations are tracked independently."""
        # Max out one operation
        for i in range(3):
            retrigger_tracker.record_retrigger("TEST-1", "start_work", "attempt")
        
        # Different operation should still be allowed
        can_retrigger, reason = retrigger_tracker.can_retrigger("TEST-1", "complete_work")
        assert can_retrigger is True
        assert reason is None
    
    def test_different_issues_tracked_separately(self, retrigger_tracker):
        """Test that different issues are tracked independently."""
        # Max out one issue
        for i in range(3):
            retrigger_tracker.record_retrigger("TEST-1", "start_work", "attempt")
        
        # Different issue should still be allowed
        can_retrigger, reason = retrigger_tracker.can_retrigger("TEST-2", "start_work")
        assert can_retrigger is True
        assert reason is None
    
    def test_window_cleanup(self, retrigger_tracker):
        """Test that old attempts outside the window are cleaned up."""
        # Record attempts with old timestamps
        key = ("TEST-1", "start_work")
        old_time = datetime.now() - timedelta(seconds=120)  # 2 minutes ago
        
        for i in range(3):
            attempt = RetriggerAttempt(
                timestamp=old_time,
                operation="start_work",
                issue_key="TEST-1",
                status="attempt",
            )
            if key not in retrigger_tracker._attempts:
                retrigger_tracker._attempts[key] = []
            retrigger_tracker._attempts[key].append(attempt)
        
        # Should be cleaned up when checking
        can_retrigger, reason = retrigger_tracker.can_retrigger("TEST-1", "start_work")
        assert can_retrigger is True
        assert retrigger_tracker.get_retrigger_count("TEST-1", "start_work") == 0
    
    def test_cooldown_period(self, retrigger_tracker):
        """Test that cooldown period is enforced after hitting limit."""
        # Max out retriggers
        for i in range(3):
            retrigger_tracker.record_retrigger("TEST-1", "start_work", "attempt")
        
        # Trigger cooldown by checking
        can_retrigger, reason = retrigger_tracker.can_retrigger("TEST-1", "start_work")
        assert can_retrigger is False
        assert "cooldown" in reason.lower()
        
        # Still in cooldown on next check
        can_retrigger, reason = retrigger_tracker.can_retrigger("TEST-1", "start_work")
        assert can_retrigger is False
        assert "cooldown" in reason.lower()
    
    def test_cooldown_expiry(self, retrigger_tracker):
        """Test that cooldown expires after configured period."""
        key = ("TEST-1", "start_work")
        
        # Set cooldown to expire in the past
        past_time = datetime.now() - timedelta(seconds=1)
        retrigger_tracker._cooldown_until[key] = past_time
        
        # Should be allowed again
        can_retrigger, reason = retrigger_tracker.can_retrigger("TEST-1", "start_work")
        assert can_retrigger is True
        assert key not in retrigger_tracker._cooldown_until
    
    def test_reset_specific_operation(self, retrigger_tracker):
        """Test resetting a specific operation."""
        # Record multiple attempts
        retrigger_tracker.record_retrigger("TEST-1", "start_work", "attempt")
        retrigger_tracker.record_retrigger("TEST-1", "complete_work", "attempt")
        
        # Reset one operation
        retrigger_tracker.reset_retriggers("TEST-1", "start_work")
        
        # Should be cleared
        assert retrigger_tracker.get_retrigger_count("TEST-1", "start_work") == 0
        
        # Other operation should still exist
        assert retrigger_tracker.get_retrigger_count("TEST-1", "complete_work") == 1
    
    def test_reset_all_operations(self, retrigger_tracker):
        """Test resetting all operations for an issue."""
        # Record multiple operations
        retrigger_tracker.record_retrigger("TEST-1", "start_work", "attempt")
        retrigger_tracker.record_retrigger("TEST-1", "complete_work", "attempt")
        retrigger_tracker.record_retrigger("TEST-1", "move_to_review", "attempt")
        
        # Reset all
        retrigger_tracker.reset_retriggers("TEST-1")
        
        # All should be cleared
        assert retrigger_tracker.get_retrigger_count("TEST-1", "start_work") == 0
        assert retrigger_tracker.get_retrigger_count("TEST-1", "complete_work") == 0
        assert retrigger_tracker.get_retrigger_count("TEST-1", "move_to_review") == 0
    
    def test_get_stats(self, retrigger_tracker):
        """Test getting tracker statistics."""
        # Record some attempts
        retrigger_tracker.record_retrigger("TEST-1", "start_work", "attempt")
        retrigger_tracker.record_retrigger("TEST-1", "start_work", "attempt")
        retrigger_tracker.record_retrigger("TEST-2", "complete_work", "attempt")
        
        stats = retrigger_tracker.get_stats()
        
        assert stats["tracked_operations"] == 2
        assert stats["total_attempts"] == 3
        assert stats["max_retriggers"] == 3
        assert stats["window_seconds"] == 60
        assert stats["cooldown_seconds"] == 30
    
    def test_get_key(self, retrigger_tracker):
        """Test key generation."""
        key1 = retrigger_tracker._get_key("TEST-1", "start_work")
        key2 = retrigger_tracker._get_key("TEST-1", "start_work")
        key3 = retrigger_tracker._get_key("TEST-2", "start_work")
        
        assert key1 == key2
        assert key1 != key3
        assert isinstance(key1, tuple)


# ── JiraRetryClient Tests ─────────────────────────────────────────────────────────────


class TestJiraRetryClient:
    """Test JiraRetryClient retry logic."""
    
    def test_create_auth_headers(self, retry_client):
        """Test authentication header creation."""
        headers = retry_client._create_auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")
        assert "Accept" in headers
        assert "Content-Type" in headers
    
    def test_calculate_delay_exponential(self, retry_client):
        """Test exponential backoff delay calculation."""
        # Base delay is 0.1, exponential base is 2
        delay_0 = retry_client._calculate_delay(0)
        delay_1 = retry_client._calculate_delay(1)
        delay_2 = retry_client._calculate_delay(2)
        
        # Should roughly double each time (with jitter)
        # delay_0 ≈ 0.1, delay_1 ≈ 0.2, delay_2 ≈ 0.4
        assert 0.05 < delay_0 < 0.15  # 0.1 ± 25% jitter
        assert 0.15 < delay_1 < 0.25  # 0.2 ± 25% jitter
        assert 0.3 < delay_2 < 0.5    # 0.4 ± 25% jitter
    
    def test_calculate_delay_max_cap(self):
        """Test that delay is capped at max_delay."""
        client = JiraRetryClient(base_delay=1.0, max_delay=5.0)
        
        # With exponential base 2, after a few attempts we should hit the cap
        delay_10 = client._calculate_delay(10)  # 2^10 = 1024 seconds
        
        # Should be capped at max_delay (5.0) with jitter
        assert 3.75 < delay_10 < 6.25  # 5.0 ± 25% jitter
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success_first_attempt(self, retry_client):
        """Test successful request on first attempt."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            response = await retry_client._execute_with_retry(
                operation="Test operation",
                url="https://test.atlassian.net/rest/api/3/issue/TEST-1",
                method="GET",
            )
            
            assert response.status_code == 200
            assert mock_client.request.call_count == 1
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_succeeds_after_retries(self, retry_client):
        """Test successful request after initial failures."""
        # Fail twice, then succeed
        responses = [
            MagicMock(status_code=503),
            MagicMock(status_code=503),
            MagicMock(status_code=200, json=lambda: {"success": True}),
        ]
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.request.side_effect = responses
            mock_client_class.return_value = mock_client
            
            response = await retry_client._execute_with_retry(
                operation="Test operation",
                url="https://test.atlassian.net/rest/api/3/issue/TEST-1",
                method="GET",
            )
            
            assert response.status_code == 200
            assert mock_client.request.call_count == 3
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_max_retries_exceeded(self, retry_client):
        """Test that max retries are respected."""
        mock_response = MagicMock(status_code=503)
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            with patch("asyncio.sleep"):  # Speed up test
                with pytest.raises(httpx.HTTPStatusError):
                    await retry_client._execute_with_retry(
                        operation="Test operation",
                        url="https://test.atlassian.net/rest/api/3/issue/TEST-1",
                        method="GET",
                    )
            
            # Should try max_retries + 1 times (initial + retries)
            assert mock_client.request.call_count == retry_client.max_retries + 1
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_non_retryable_error(self, retry_client):
        """Test that non-retryable errors fail immediately."""
        mock_response = MagicMock(status_code=400)
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_response
        )
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            with pytest.raises(httpx.HTTPStatusError):
                await retry_client._execute_with_retry(
                    operation="Test operation",
                    url="https://test.atlassian.net/rest/api/3/issue/TEST-1",
                    method="GET",
                )
            
            # Should only try once (no retries for 400 errors)
            assert mock_client.request.call_count == 1
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_timeout_error(self, retry_client):
        """Test retry on timeout errors."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.request.side_effect = [
                httpx.TimeoutException("Timeout"),
                httpx.TimeoutException("Timeout"),
                MagicMock(status_code=200, json=lambda: {"success": True}),
            ]
            mock_client_class.return_value = mock_client
            
            with patch("asyncio.sleep"):  # Speed up test
                response = await retry_client._execute_with_retry(
                    operation="Test operation",
                    url="https://test.atlassian.net/rest/api/3/issue/TEST-1",
                    method="GET",
                )
            
            assert response.status_code == 200
            assert mock_client.request.call_count == 3
    
    @pytest.mark.asyncio
    async def test_get_issue(self, retry_client):
        """Test get_issue method."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "key": "TEST-1",
            "fields": {"summary": "Test issue", "status": {"name": "To Do"}},
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            issue = await retry_client.get_issue("TEST-1")
            
            assert issue["key"] == "TEST-1"
            assert issue["fields"]["summary"] == "Test issue"
    
    @pytest.mark.asyncio
    async def test_get_transitions(self, retry_client):
        """Test get_transitions method."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "transitions": [
                {"id": "11", "name": "Start Progress", "to": {"name": "In Progress"}},
                {"id": "21", "name": "Done", "to": {"name": "Done"}},
            ]
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            transitions = await retry_client.get_transitions("TEST-1")
            
            assert len(transitions) == 2
            assert transitions[0]["name"] == "Start Progress"
    
    @pytest.mark.asyncio
    async def test_transition_issue_success(self, retry_client):
        """Test successful issue transition."""
        # Mock transition response
        transition_response = MagicMock(status_code=204)
        
        # Mock get_issue response
        issue_response = MagicMock()
        issue_response.status_code = 200
        issue_response.json.return_value = {
            "key": "TEST-1",
            "fields": {"status": {"name": "In Progress"}},
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.request.side_effect = [transition_response, issue_response]
            mock_client_class.return_value = mock_client
            
            result = await retry_client.transition_issue(
                issue_key="TEST-1",
                transition_id="11",
            )
            
            assert result.status == TransitionStatus.SUCCESS
            assert result.issue_key == "TEST-1"
            assert result.final_status == "In Progress"
    
    @pytest.mark.asyncio
    async def test_transition_issue_by_name(self, retry_client):
        """Test transition by status name."""
        # Mock get_transitions response
        transitions_response = MagicMock()
        transitions_response.status_code = 200
        transitions_response.json.return_value = {
            "transitions": [
                {"id": "11", "name": "Start Progress", "to": {"name": "In Progress"}},
            ]
        }
        
        # Mock transition response
        transition_response = MagicMock(status_code=204)
        
        # Mock get_issue response
        issue_response = MagicMock()
        issue_response.status_code = 200
        issue_response.json.return_value = {
            "key": "TEST-1",
            "fields": {"status": {"name": "In Progress"}},
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.request.side_effect = [
                transitions_response,
                transition_response,
                issue_response,
            ]
            mock_client_class.return_value = mock_client
            
            result = await retry_client.transition_issue_by_name(
                issue_key="TEST-1",
                target_status="In Progress",
            )
            
            assert result.status == TransitionStatus.SUCCESS
            assert result.transition_name == "Start Progress"
    
    @pytest.mark.asyncio
    async def test_transition_issue_by_name_not_found(self, retry_client):
        """Test transition by name when status not available."""
        transitions_response = MagicMock()
        transitions_response.status_code = 200
        transitions_response.json.return_value = {
            "transitions": [
                {"id": "11", "name": "Start Progress", "to": {"name": "In Progress"}},
            ]
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.request.return_value = transitions_response
            mock_client_class.return_value = mock_client
            
            result = await retry_client.transition_issue_by_name(
                issue_key="TEST-1",
                target_status="Done",
            )
            
            assert result.status == TransitionStatus.FAILED
            assert "No transition found" in result.error_message
    
    @pytest.mark.asyncio
    async def test_bulk_transition(self, retry_client):
        """Test bulk transition operations."""
        # Mock get_transitions
        transitions_response = MagicMock()
        transitions_response.status_code = 200
        transitions_response.json.return_value = {
            "transitions": [
                {"id": "11", "name": "Start Progress", "to": {"name": "In Progress"}},
            ]
        }
        
        # Mock transition responses
        transition_response = MagicMock(status_code=204)
        
        # Mock get_issue responses
        issue_response = MagicMock()
        issue_response.status_code = 200
        issue_response.json.return_value = {
            "fields": {"status": {"name": "In Progress"}},
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            # Each transition: get_transitions, transition, get_issue
            mock_client.request.side_effect = [
                transitions_response, transition_response, issue_response,
                transitions_response, transition_response, issue_response,
            ]
            mock_client_class.return_value = mock_client
            
            results = await retry_client.bulk_transition([
                {"issue_key": "TEST-1", "target_status": "In Progress"},
                {"issue_key": "TEST-2", "target_status": "In Progress"},
            ])
            
            assert len(results) == 2
            assert all(r.status == TransitionStatus.SUCCESS for r in results)


# ── ManagerAgent Tests ────────────────────────────────────────────────────────────────


class TestManagerAgent:
    """Test ManagerAgent workflow methods."""
    
    @pytest.mark.asyncio
    async def test_start_work(self, manager_agent):
        """Test start_work method."""
        with patch.object(
            manager_agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.SUCCESS,
                issue_key="TEST-1",
                final_status="In Progress",
            )
            
            result = await manager_agent.start_work("TEST-1")
            
            assert result.status == TransitionStatus.SUCCESS
            mock_transition.assert_called_once()
            call_kwargs = mock_transition.call_args.kwargs
            assert call_kwargs["target_status"] == "In Progress"
    
    @pytest.mark.asyncio
    async def test_start_work_with_assignee(self, manager_agent):
        """Test start_work with assignee."""
        with patch.object(
            manager_agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.SUCCESS,
                issue_key="TEST-1",
                final_status="In Progress",
            )
            
            result = await manager_agent.start_work("TEST-1", assignee="john.doe")
            
            assert result.status == TransitionStatus.SUCCESS
            call_kwargs = mock_transition.call_args.kwargs
            assert call_kwargs["fields"]["assignee"]["name"] == "john.doe"
    
    @pytest.mark.asyncio
    async def test_complete_work(self, manager_agent):
        """Test complete_work method."""
        with patch.object(
            manager_agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.SUCCESS,
                issue_key="TEST-1",
                final_status="Done",
            )
            
            result = await manager_agent.complete_work("TEST-1")
            
            assert result.status == TransitionStatus.SUCCESS
            call_kwargs = mock_transition.call_args.kwargs
            assert call_kwargs["target_status"] == "Done"
    
    @pytest.mark.asyncio
    async def test_move_to_code_review(self, manager_agent):
        """Test move_to_code_review method."""
        with patch.object(
            manager_agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.SUCCESS,
                issue_key="TEST-1",
                final_status="Code Review",
            )
            
            result = await manager_agent.move_to_code_review("TEST-1")
            
            assert result.status == TransitionStatus.SUCCESS
            call_kwargs = mock_transition.call_args.kwargs
            assert call_kwargs["target_status"] == "Code Review"
    
    @pytest.mark.asyncio
    async def test_move_to_testing(self, manager_agent):
        """Test move_to_testing method."""
        with patch.object(
            manager_agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.SUCCESS,
                issue_key="TEST-1",
                final_status="Testing",
            )
            
            result = await manager_agent.move_to_testing("TEST-1")
            
            assert result.status == TransitionStatus.SUCCESS
    
    @pytest.mark.asyncio
    async def test_move_to_testing_fallback_to_qa(self, manager_agent):
        """Test move_to_testing falls back to QA if Testing not available."""
        with patch.object(
            manager_agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            # First call fails (Testing not found), second succeeds (QA found)
            mock_transition.side_effect = [
                TransitionResult(
                    status=TransitionStatus.FAILED,
                    issue_key="TEST-1",
                    error_message="No transition found to 'Testing'",
                ),
                TransitionResult(
                    status=TransitionStatus.SUCCESS,
                    issue_key="TEST-1",
                    final_status="QA",
                ),
            ]
            
            result = await manager_agent.move_to_testing("TEST-1")
            
            assert result.status == TransitionStatus.SUCCESS
            assert mock_transition.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_issue_status(self, manager_agent):
        """Test get_issue_status method."""
        with patch.object(
            manager_agent.client, "get_issue", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = {
                "fields": {"status": {"name": "In Progress"}},
            }
            
            status = await manager_agent.get_issue_status("TEST-1")
            
            assert status == "In Progress"
    
    @pytest.mark.asyncio
    async def test_get_issue_status_error(self, manager_agent):
        """Test get_issue_status handles errors."""
        with patch.object(
            manager_agent.client, "get_issue", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = Exception("API error")
            
            status = await manager_agent.get_issue_status("TEST-1")
            
            assert status is None


# ── Retrigger Protection Tests ────────────────────────────────────────────────────────


class TestRetriggerProtection:
    """Test Manager Agent's retrigger protection functionality."""
    
    @pytest.mark.asyncio
    async def test_retrigger_protection_enabled(self, mock_env):
        """Test that retrigger protection is enabled by default."""
        agent = ManagerAgent(max_retriggers=2, retrigger_window=60)
        assert agent.enable_retrigger_protection is True
        assert agent.retrigger_tracker is not None
    
    @pytest.mark.asyncio
    async def test_retrigger_protection_disabled(self, mock_env):
        """Test disabling retrigger protection."""
        agent = ManagerAgent(enable_retrigger_protection=False)
        
        with patch.object(
            agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.SUCCESS,
                issue_key="TEST-1",
            )
            
            # Should allow unlimited retriggers when disabled
            for i in range(10):
                result = await agent.start_work("TEST-1")
                assert result.status == TransitionStatus.SUCCESS
    
    @pytest.mark.asyncio
    async def test_retrigger_count_increments(self, mock_env):
        """Test that retrigger count increments correctly."""
        agent = ManagerAgent(max_retriggers=3, retrigger_window=60)
        
        with patch.object(
            agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.SUCCESS,
                issue_key="TEST-1",
            )
            
            result1 = await agent.start_work("TEST-1")
            assert result1.retrigger_count == 1
            
            result2 = await agent.start_work("TEST-1")
            assert result2.retrigger_count == 2
            
            result3 = await agent.start_work("TEST-1")
            assert result3.retrigger_count == 3
    
    @pytest.mark.asyncio
    async def test_retrigger_limit_exceeded(self, mock_env):
        """Test that retriggers are blocked after hitting limit."""
        agent = ManagerAgent(max_retriggers=3, retrigger_window=60)
        
        with patch.object(
            agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.SUCCESS,
                issue_key="TEST-1",
            )
            
            # Allow first 3 attempts
            for i in range(3):
                result = await agent.start_work("TEST-1")
                assert result.status == TransitionStatus.SUCCESS
            
            # 4th attempt should be blocked
            result4 = await agent.start_work("TEST-1")
            assert result4.status == TransitionStatus.MAX_RETRIGGERS_EXCEEDED
            assert "Maximum retrigger limit" in result4.error_message
            
            # Client should not have been called on 4th attempt
            assert mock_transition.call_count == 3
    
    @pytest.mark.asyncio
    async def test_retrigger_different_operations_independent(self, mock_env):
        """Test that different operations are tracked independently."""
        agent = ManagerAgent(max_retriggers=2, retrigger_window=60)
        
        with patch.object(
            agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.SUCCESS,
                issue_key="TEST-1",
            )
            
            # Max out start_work
            await agent.start_work("TEST-1")
            await agent.start_work("TEST-1")
            
            # complete_work should still be allowed
            result = await agent.complete_work("TEST-1")
            assert result.status == TransitionStatus.SUCCESS
            
            # But 3rd start_work should be blocked
            result = await agent.start_work("TEST-1")
            assert result.status == TransitionStatus.MAX_RETRIGGERS_EXCEEDED
    
    @pytest.mark.asyncio
    async def test_retrigger_reset(self, mock_env):
        """Test resetting retrigger tracking."""
        agent = ManagerAgent(max_retriggers=2, retrigger_window=60)
        
        with patch.object(
            agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.SUCCESS,
                issue_key="TEST-1",
            )
            
            # Max out retriggers
            await agent.start_work("TEST-1")
            await agent.start_work("TEST-1")
            
            # Next should be blocked
            result = await agent.start_work("TEST-1")
            assert result.status == TransitionStatus.MAX_RETRIGGERS_EXCEEDED
            
            # Reset and try again
            agent.reset_retriggers("TEST-1", "start_work")
            
            result = await agent.start_work("TEST-1")
            assert result.status == TransitionStatus.SUCCESS
    
    @pytest.mark.asyncio
    async def test_retrigger_stats(self, mock_env):
        """Test getting retrigger statistics."""
        agent = ManagerAgent(max_retriggers=3, retrigger_window=60)
        
        with patch.object(
            agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.SUCCESS,
                issue_key="TEST-1",
            )
            
            await agent.start_work("TEST-1")
            await agent.complete_work("TEST-1")
            await agent.move_to_code_review("TEST-2")
            
            stats = agent.get_retrigger_stats()
            
            assert stats["tracked_operations"] == 3
            assert stats["total_attempts"] == 3
            assert stats["max_retriggers"] == 3
    
    @pytest.mark.asyncio
    async def test_all_operations_have_protection(self, mock_env):
        """Test that all Manager Agent operations have retrigger protection."""
        agent = ManagerAgent(max_retriggers=1, retrigger_window=60)
        
        with patch.object(
            agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.SUCCESS,
                issue_key="TEST-1",
            )
            
            # Test start_work
            await agent.start_work("TEST-1")
            result = await agent.start_work("TEST-1")
            assert result.status == TransitionStatus.MAX_RETRIGGERS_EXCEEDED
            
            # Test complete_work
            await agent.complete_work("TEST-2")
            result = await agent.complete_work("TEST-2")
            assert result.status == TransitionStatus.MAX_RETRIGGERS_EXCEEDED
            
            # Test move_to_code_review
            await agent.move_to_code_review("TEST-3")
            result = await agent.move_to_code_review("TEST-3")
            assert result.status == TransitionStatus.MAX_RETRIGGERS_EXCEEDED
            
            # Test move_to_testing
            await agent.move_to_testing("TEST-4")
            result = await agent.move_to_testing("TEST-4")
            assert result.status == TransitionStatus.MAX_RETRIGGERS_EXCEEDED


# ── Diff Review Tests ─────────────────────────────────────────────────────────────────


class TestDiffReview:
    """Test Manager Agent's diff review capabilities."""
    
    def test_review_diff_small(self, manager_agent):
        """Test reviewing a small diff that doesn't need truncation."""
        result = manager_agent.review_diff(SAMPLE_NEW_FILE_DIFF)
        
        assert isinstance(result, DiffReviewResult)
        assert not result.was_truncated
        assert result.has_new_files
        assert len(result.new_files_summary) == 1
        assert result.new_files_summary[0]["path"] == "tools/new_feature.py"
    
    def test_review_diff_large(self, manager_agent):
        """Test reviewing a large diff that needs truncation."""
        # Create a very large diff
        large_diff = SAMPLE_NEW_FILE_DIFF * 100
        
        # Use small max_chars to force truncation
        agent = ManagerAgent(max_retries=3, base_delay=0.1, diff_max_chars=1000)
        result = agent.review_diff(large_diff)
        
        assert result.was_truncated
        assert len(result.truncated_diff) <= 2000  # Some buffer for summaries
    
    def test_review_diff_new_files_prioritized(self, manager_agent):
        """Test that new files are prioritized in truncation."""
        mixed_diff = SAMPLE_NEW_FILE_DIFF + "\n\n" + SAMPLE_MODIFIED_FILE_DIFF
        
        result = manager_agent.review_diff(mixed_diff)
        
        assert result.has_new_files
        assert "tools/new_feature.py" in result.truncated_diff
    
    def test_review_diff_with_comments(self, manager_agent):
        """Test that review comments are generated."""
        result = manager_agent.review_diff(
            SAMPLE_NEW_FILE_DIFF,
            generate_comments=True,
        )
        
        assert len(result.review_comments) > 0
        # Should comment on new files
        assert any("new file" in comment.lower() for comment in result.review_comments)
    
    def test_review_diff_without_comments(self, manager_agent):
        """Test diff review without generating comments."""
        result = manager_agent.review_diff(
            SAMPLE_NEW_FILE_DIFF,
            generate_comments=False,
        )
        
        assert len(result.review_comments) == 0
    
    def test_review_comments_for_large_pr(self, manager_agent):
        """Test that review comments mention PR size for large PRs."""
        # Create a diff with many files
        large_diff = "\n\n".join([
            SAMPLE_MODIFIED_FILE_DIFF.replace("existing.py", f"file{i}.py")
            for i in range(15)
        ])
        
        result = manager_agent.review_diff(large_diff, generate_comments=True)
        
        # Should warn about large PR
        assert any("large PR" in comment.lower() for comment in result.review_comments)
    
    @pytest.mark.asyncio
    async def test_review_and_comment_pr(self, manager_agent):
        """Test reviewing a PR and posting to Jira."""
        with patch.object(
            manager_agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.SUCCESS,
                issue_key="TEST-1",
                final_status="Code Review",
            )
            
            review_result, transition_result = await manager_agent.review_and_comment_pr(
                issue_key="TEST-1",
                diff_text=SAMPLE_NEW_FILE_DIFF,
            )
            
            assert isinstance(review_result, DiffReviewResult)
            assert transition_result.status == TransitionStatus.SUCCESS
            
            # Check that comment was passed
            call_kwargs = mock_transition.call_args.kwargs
            assert "comment" in call_kwargs
            assert "Code Review" in call_kwargs["comment"]
    
    def test_format_review_for_jira(self, manager_agent):
        """Test formatting review result for Jira."""
        review_result = manager_agent.review_diff(
            SAMPLE_NEW_FILE_DIFF,
            generate_comments=True,
        )
        
        jira_comment = manager_agent._format_review_for_jira(review_result)
        
        assert "Code Review" in jira_comment
        assert "Manager Agent" in jira_comment
        assert "Statistics" in jira_comment
        assert "Total files:" in jira_comment
    
    def test_diff_review_result_properties(self):
        """Test DiffReviewResult properties."""
        result = DiffReviewResult(
            truncated_diff="diff content",
            metadata={"truncated": True, "new_files_count": 2},
            new_files_summary=[{"path": "test.py"}],
            review_comments=["comment 1"],
        )
        
        assert result.has_new_files is True
        assert result.was_truncated is True
        
        # Test with no new files
        result_no_new = DiffReviewResult(
            truncated_diff="diff content",
            metadata={"truncated": False},
            new_files_summary=[],
            review_comments=[],
        )
        
        assert result_no_new.has_new_files is False
        assert result_no_new.was_truncated is False


# ── Factory Function Tests ────────────────────────────────────────────────────────────


def test_create_manager_agent(mock_env):
    """Test factory function."""
    agent = create_manager_agent()
    
    assert isinstance(agent, ManagerAgent)
    assert agent.client.max_retries == DEFAULT_MAX_RETRIES
    assert agent.retrigger_tracker.max_retriggers == DEFAULT_MAX_RETRIGGERS


def test_create_manager_agent_custom_params(mock_env):
    """Test factory function with custom parameters."""
    agent = create_manager_agent(
        max_retries=10,
        base_delay=2.0,
        diff_max_chars=100000,
        max_retriggers=5,
        retrigger_window=120,
    )
    
    assert agent.client.max_retries == 10
    assert agent.client.base_delay == 2.0
    assert agent.diff_max_chars == 100000
    assert agent.retrigger_tracker.max_retriggers == 5
    assert agent.retrigger_tracker.window_seconds == 120


def test_create_manager_agent_disable_protection(mock_env):
    """Test creating agent with protection disabled."""
    agent = create_manager_agent(enable_retrigger_protection=False)
    
    assert agent.enable_retrigger_protection is False


# ── Integration Tests ─────────────────────────────────────────────────────────────────


class TestIntegration:
    """Integration tests for realistic scenarios."""
    
    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self, retry_client):
        """Test that rate limit errors trigger retry."""
        responses = [
            MagicMock(status_code=429),  # Rate limited
            MagicMock(status_code=200, json=lambda: {"success": True}),
        ]
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.request.side_effect = responses
            mock_client_class.return_value = mock_client
            
            with patch("asyncio.sleep"):  # Speed up test
                response = await retry_client._execute_with_retry(
                    operation="Test",
                    url="https://test.atlassian.net/test",
                    method="GET",
                )
            
            assert response.status_code == 200
            assert mock_client.request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_workflow_sequence(self, manager_agent):
        """Test a complete workflow sequence."""
        with patch.object(
            manager_agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            # Mock all transitions to succeed
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.SUCCESS,
                issue_key="TEST-1",
            )
            
            # Start work
            result1 = await manager_agent.start_work("TEST-1")
            assert result1.status == TransitionStatus.SUCCESS
            
            # Move to code review
            result2 = await manager_agent.move_to_code_review("TEST-1")
            assert result2.status == TransitionStatus.SUCCESS
            
            # Move to testing
            result3 = await manager_agent.move_to_testing("TEST-1")
            assert result3.status == TransitionStatus.SUCCESS
            
            # Complete work
            result4 = await manager_agent.complete_work("TEST-1")
            assert result4.status == TransitionStatus.SUCCESS
            
            assert mock_transition.call_count == 4
    
    @pytest.mark.asyncio
    async def test_full_pr_review_workflow(self, manager_agent):
        """Test complete PR review and transition workflow."""
        # Create a realistic multi-file diff
        pr_diff = "\n\n".join([
            SAMPLE_NEW_FILE_DIFF,
            SAMPLE_MODIFIED_FILE_DIFF,
        ])
        
        with patch.object(
            manager_agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.SUCCESS,
                issue_key="TEST-1",
                final_status="Code Review",
            )
            
            review_result, transition_result = await manager_agent.review_and_comment_pr(
                issue_key="TEST-1",
                diff_text=pr_diff,
            )
            
            # Verify review result
            assert review_result.has_new_files
            assert len(review_result.new_files_summary) == 1
            assert len(review_result.review_comments) > 0
            
            # Verify transition
            assert transition_result.status == TransitionStatus.SUCCESS
            assert transition_result.final_status == "Code Review"
            
            # Verify comment was posted
            call_kwargs = mock_transition.call_args.kwargs
            assert "comment" in call_kwargs
            comment = call_kwargs["comment"]
            assert "Code Review" in comment
            assert "new file" in comment.lower()
    
    @pytest.mark.asyncio
    async def test_retrigger_protection_in_workflow(self, mock_env):
        """Test retrigger protection in a realistic workflow."""
        agent = ManagerAgent(max_retriggers=2, retrigger_window=60)
        
        with patch.object(
            agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.SUCCESS,
                issue_key="TEST-1",
            )
            
            # Simulate a buggy workflow that keeps calling start_work
            results = []
            for i in range(5):
                result = await agent.start_work("TEST-1")
                results.append(result)
            
            # First 2 should succeed
            assert results[0].status == TransitionStatus.SUCCESS
            assert results[1].status == TransitionStatus.SUCCESS
            
            # Remaining should be blocked
            assert results[2].status == TransitionStatus.MAX_RETRIGGERS_EXCEEDED
            assert results[3].status == TransitionStatus.MAX_RETRIGGERS_EXCEEDED
            assert results[4].status == TransitionStatus.MAX_RETRIGGERS_EXCEEDED
            
            # Client should only have been called twice
            assert mock_transition.call_count == 2
