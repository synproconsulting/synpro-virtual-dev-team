"""
Tests for Manager Agent with exponential backoff retry logic and diff review.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from datetime import datetime

from manager_agent import (
    JiraRetryClient,
    ManagerAgent,
    TransitionStatus,
    TransitionResult,
    DiffReviewResult,
    OperationState,
    RetriggerLimitExceeded,
    create_manager_agent,
    DEFAULT_MAX_RETRIES,
    DEFAULT_BASE_DELAY,
    DEFAULT_MAX_RETRIGGER_COUNT,
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
    return ManagerAgent(max_retries=3, base_delay=0.1, max_retrigger_count=3)


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


# ── OperationState Tests ──────────────────────────────────────────────────────────────


class TestOperationState:
    """Test OperationState tracking."""
    
    def test_operation_state_creation(self):
        """Test creating an operation state."""
        state = OperationState(
            operation_id="test_op:TEST-1",
            issue_key="TEST-1",
            operation_type="test_op",
        )
        
        assert state.operation_id == "test_op:TEST-1"
        assert state.issue_key == "TEST-1"
        assert state.operation_type == "test_op"
        assert state.trigger_count == 0
        assert len(state.error_history) == 0
    
    def test_increment_trigger(self):
        """Test incrementing trigger count."""
        state = OperationState(
            operation_id="test_op:TEST-1",
            issue_key="TEST-1",
            operation_type="test_op",
        )
        
        count = state.increment_trigger()
        assert count == 1
        assert state.trigger_count == 1
        
        count = state.increment_trigger(error_message="Test error")
        assert count == 2
        assert state.trigger_count == 2
        assert len(state.error_history) == 1
        assert state.error_history[0] == "Test error"
    
    def test_is_limit_exceeded(self):
        """Test checking if limit is exceeded."""
        state = OperationState(
            operation_id="test_op:TEST-1",
            issue_key="TEST-1",
            operation_type="test_op",
        )
        
        assert not state.is_limit_exceeded(3)
        
        state.increment_trigger()
        assert not state.is_limit_exceeded(3)
        
        state.increment_trigger()
        state.increment_trigger()
        assert state.is_limit_exceeded(3)
    
    def test_get_summary(self):
        """Test getting operation state summary."""
        state = OperationState(
            operation_id="test_op:TEST-1",
            issue_key="TEST-1",
            operation_type="test_op",
        )
        
        state.increment_trigger(error_message="Error 1")
        state.increment_trigger(error_message="Error 2")
        
        summary = state.get_summary()
        
        assert summary["operation_id"] == "test_op:TEST-1"
        assert summary["issue_key"] == "TEST-1"
        assert summary["operation_type"] == "test_op"
        assert summary["trigger_count"] == 2
        assert summary["error_count"] == 2
        assert len(summary["recent_errors"]) == 2


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


# ── ManagerAgent Retrigger Tests ──────────────────────────────────────────────────────


class TestManagerAgentRetrigger:
    """Test Manager Agent retrigger loop protection."""
    
    def test_get_operation_id(self, manager_agent):
        """Test operation ID generation."""
        op_id = manager_agent._get_operation_id("start_work", "TEST-1")
        assert op_id == "start_work:TEST-1"
    
    def test_check_and_increment_retrigger_first_call(self, manager_agent):
        """Test first retrigger check."""
        count = manager_agent._check_and_increment_retrigger("start_work", "TEST-1")
        
        assert count == 1
        assert "start_work:TEST-1" in manager_agent._operation_states
    
    def test_check_and_increment_retrigger_multiple_calls(self, manager_agent):
        """Test multiple retrigger checks."""
        count1 = manager_agent._check_and_increment_retrigger("start_work", "TEST-1")
        count2 = manager_agent._check_and_increment_retrigger("start_work", "TEST-1")
        count3 = manager_agent._check_and_increment_retrigger("start_work", "TEST-1")
        
        assert count1 == 1
        assert count2 == 2
        assert count3 == 3
    
    def test_check_and_increment_retrigger_limit_exceeded(self, manager_agent):
        """Test that exception is raised when limit exceeded."""
        # Max is 3, so 4th call should raise
        manager_agent._check_and_increment_retrigger("start_work", "TEST-1")
        manager_agent._check_and_increment_retrigger("start_work", "TEST-1")
        manager_agent._check_and_increment_retrigger("start_work", "TEST-1")
        
        with pytest.raises(RetriggerLimitExceeded) as exc_info:
            manager_agent._check_and_increment_retrigger("start_work", "TEST-1")
        
        assert "Retrigger limit exceeded" in str(exc_info.value)
        assert "TEST-1" in str(exc_info.value)
    
    def test_check_and_increment_retrigger_with_error_message(self, manager_agent):
        """Test retrigger tracking with error messages."""
        manager_agent._check_and_increment_retrigger(
            "start_work", "TEST-1", error_message="Error 1"
        )
        manager_agent._check_and_increment_retrigger(
            "start_work", "TEST-1", error_message="Error 2"
        )
        
        state = manager_agent._operation_states["start_work:TEST-1"]
        assert len(state.error_history) == 2
        assert "Error 1" in state.error_history
        assert "Error 2" in state.error_history
    
    def test_reset_retrigger_count(self, manager_agent):
        """Test resetting retrigger count."""
        manager_agent._check_and_increment_retrigger("start_work", "TEST-1")
        manager_agent._check_and_increment_retrigger("start_work", "TEST-1")
        
        assert "start_work:TEST-1" in manager_agent._operation_states
        
        manager_agent._reset_retrigger_count("start_work", "TEST-1")
        
        assert "start_work:TEST-1" not in manager_agent._operation_states
    
    def test_get_operation_state(self, manager_agent):
        """Test getting operation state."""
        # No state initially
        state = manager_agent.get_operation_state("start_work", "TEST-1")
        assert state is None
        
        # Create some state
        manager_agent._check_and_increment_retrigger("start_work", "TEST-1", "Error")
        
        state = manager_agent.get_operation_state("start_work", "TEST-1")
        assert state is not None
        assert state["operation_type"] == "start_work"
        assert state["issue_key"] == "TEST-1"
        assert state["trigger_count"] == 1
    
    def test_get_all_operation_states(self, manager_agent):
        """Test getting all operation states."""
        # Create multiple states
        manager_agent._check_and_increment_retrigger("start_work", "TEST-1")
        manager_agent._check_and_increment_retrigger("complete_work", "TEST-2")
        manager_agent._check_and_increment_retrigger("start_work", "TEST-3")
        
        states = manager_agent.get_all_operation_states()
        
        assert len(states) == 3
        operation_types = [s["operation_type"] for s in states]
        assert "start_work" in operation_types
        assert "complete_work" in operation_types
    
    def test_clear_all_operation_states(self, manager_agent):
        """Test clearing all operation states."""
        manager_agent._check_and_increment_retrigger("start_work", "TEST-1")
        manager_agent._check_and_increment_retrigger("complete_work", "TEST-2")
        
        count = manager_agent.clear_all_operation_states()
        
        assert count == 2
        assert len(manager_agent._operation_states) == 0
    
    def test_different_operations_tracked_separately(self, manager_agent):
        """Test that different operations are tracked separately."""
        manager_agent._check_and_increment_retrigger("start_work", "TEST-1")
        manager_agent._check_and_increment_retrigger("start_work", "TEST-1")
        
        manager_agent._check_and_increment_retrigger("complete_work", "TEST-1")
        
        # start_work should be at count 2
        start_state = manager_agent._operation_states["start_work:TEST-1"]
        assert start_state.trigger_count == 2
        
        # complete_work should be at count 1
        complete_state = manager_agent._operation_states["complete_work:TEST-1"]
        assert complete_state.trigger_count == 1
    
    def test_different_issues_tracked_separately(self, manager_agent):
        """Test that different issues are tracked separately."""
        manager_agent._check_and_increment_retrigger("start_work", "TEST-1")
        manager_agent._check_and_increment_retrigger("start_work", "TEST-1")
        
        manager_agent._check_and_increment_retrigger("start_work", "TEST-2")
        
        # TEST-1 should be at count 2
        state1 = manager_agent._operation_states["start_work:TEST-1"]
        assert state1.trigger_count == 2
        
        # TEST-2 should be at count 1
        state2 = manager_agent._operation_states["start_work:TEST-2"]
        assert state2.trigger_count == 1


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
            assert result.retrigger_count == 1
            mock_transition.assert_called_once()
            call_kwargs = mock_transition.call_args.kwargs
            assert call_kwargs["target_status"] == "In Progress"
    
    @pytest.mark.asyncio
    async def test_start_work_resets_on_success(self, manager_agent):
        """Test that start_work resets retrigger count on success."""
        with patch.object(
            manager_agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.SUCCESS,
                issue_key="TEST-1",
                final_status="In Progress",
            )
            
            # First call
            await manager_agent.start_work("TEST-1")
            
            # Should be reset
            assert "start_work:TEST-1" not in manager_agent._operation_states
            
            # Second call should also work (count reset)
            result = await manager_agent.start_work("TEST-1")
            assert result.retrigger_count == 1
    
    @pytest.mark.asyncio
    async def test_start_work_retrigger_limit(self, manager_agent):
        """Test start_work enforces retrigger limit."""
        with patch.object(
            manager_agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.FAILED,
                issue_key="TEST-1",
                error_message="Transition failed",
            )
            
            # First 3 attempts should work
            await manager_agent.start_work("TEST-1")
            await manager_agent.start_work("TEST-1")
            await manager_agent.start_work("TEST-1")
            
            # 4th attempt should raise
            with pytest.raises(RetriggerLimitExceeded):
                await manager_agent.start_work("TEST-1")
    
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
            assert result.retrigger_count == 1
            call_kwargs = mock_transition.call_args.kwargs
            assert call_kwargs["target_status"] == "Done"
    
    @pytest.mark.asyncio
    async def test_complete_work_retrigger_limit(self, manager_agent):
        """Test complete_work enforces retrigger limit."""
        with patch.object(
            manager_agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.FAILED,
                issue_key="TEST-1",
                error_message="Transition failed",
            )
            
            # First 3 attempts should work
            await manager_agent.complete_work("TEST-1")
            await manager_agent.complete_work("TEST-1")
            await manager_agent.complete_work("TEST-1")
            
            # 4th attempt should raise
            with pytest.raises(RetriggerLimitExceeded):
                await manager_agent.complete_work("TEST-1")
    
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
            assert result.retrigger_count == 1
            call_kwargs = mock_transition.call_args.kwargs
            assert call_kwargs["target_status"] == "Code Review"
    
    @pytest.mark.asyncio
    async def test_move_to_code_review_retrigger_limit(self, manager_agent):
        """Test move_to_code_review enforces retrigger limit."""
        with patch.object(
            manager_agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.FAILED,
                issue_key="TEST-1",
                error_message="Transition failed",
            )
            
            # First 3 attempts should work
            await manager_agent.move_to_code_review("TEST-1")
            await manager_agent.move_to_code_review("TEST-1")
            await manager_agent.move_to_code_review("TEST-1")
            
            # 4th attempt should raise
            with pytest.raises(RetriggerLimitExceeded):
                await manager_agent.move_to_code_review("TEST-1")
    
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
            assert result.retrigger_count == 1
    
    @pytest.mark.asyncio
    async def test_move_to_testing_retrigger_limit(self, manager_agent):
        """Test move_to_testing enforces retrigger limit."""
        with patch.object(
            manager_agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.FAILED,
                issue_key="TEST-1",
                error_message="Transition failed",
            )
            
            # First 3 attempts should work
            await manager_agent.move_to_testing("TEST-1")
            await manager_agent.move_to_testing("TEST-1")
            await manager_agent.move_to_testing("TEST-1")
            
            # 4th attempt should raise
            with pytest.raises(RetriggerLimitExceeded):
                await manager_agent.move_to_testing("TEST-1")
    
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
    
    @pytest.mark.asyncio
    async def test_review_and_comment_pr_enforces_retrigger_limit(self, manager_agent):
        """Test that review_and_comment_pr enforces retrigger limit."""
        with patch.object(
            manager_agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.FAILED,
                issue_key="TEST-1",
                error_message="Transition failed",
            )
            
            # First 3 attempts should work
            await manager_agent.review_and_comment_pr("TEST-1", SAMPLE_NEW_FILE_DIFF)
            await manager_agent.review_and_comment_pr("TEST-1", SAMPLE_NEW_FILE_DIFF)
            await manager_agent.review_and_comment_pr("TEST-1", SAMPLE_NEW_FILE_DIFF)
            
            # 4th attempt should raise
            with pytest.raises(RetriggerLimitExceeded):
                await manager_agent.review_and_comment_pr("TEST-1", SAMPLE_NEW_FILE_DIFF)
    
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
    assert agent.max_retrigger_count == DEFAULT_MAX_RETRIGGER_COUNT


def test_create_manager_agent_custom_params(mock_env):
    """Test factory function with custom parameters."""
    agent = create_manager_agent(
        max_retries=10,
        base_delay=2.0,
        diff_max_chars=100000,
        max_retrigger_count=5,
    )
    
    assert agent.client.max_retries == 10
    assert agent.client.base_delay == 2.0
    assert agent.diff_max_chars == 100000
    assert agent.max_retrigger_count == 5


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
    async def test_workflow_with_retrigger_protection(self, manager_agent):
        """Test workflow sequence with retrigger protection."""
        with patch.object(
            manager_agent.client, "transition_issue_by_name", new_callable=AsyncMock
        ) as mock_transition:
            # Mock transitions to fail initially
            mock_transition.return_value = TransitionResult(
                status=TransitionStatus.FAILED,
                issue_key="TEST-1",
                error_message="Temporary failure",
            )
            
            # First 3 attempts should work
            await manager_agent.start_work("TEST-1")
            await manager_agent.start_work("TEST-1")
            await manager_agent.start_work("TEST-1")
            
            # 4th attempt should raise
            with pytest.raises(RetriggerLimitExceeded):
                await manager_agent.start_work("TEST-1")
            
            # But other operations on same issue should still work
            result = await manager_agent.complete_work("TEST-1")
            assert result.retrigger_count == 1
    
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
