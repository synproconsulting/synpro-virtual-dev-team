"""
Tests for Manager Agent with exponential backoff retry logic.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from manager_agent import (
    JiraRetryClient,
    ManagerAgent,
    TransitionStatus,
    TransitionResult,
    create_manager_agent,
    DEFAULT_MAX_RETRIES,
    DEFAULT_BASE_DELAY,
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


# ── Factory Function Tests ────────────────────────────────────────────────────────────


def test_create_manager_agent(mock_env):
    """Test factory function."""
    agent = create_manager_agent()
    
    assert isinstance(agent, ManagerAgent)
    assert agent.client.max_retries == DEFAULT_MAX_RETRIES


def test_create_manager_agent_custom_params(mock_env):
    """Test factory function with custom parameters."""
    agent = create_manager_agent(max_retries=10, base_delay=2.0)
    
    assert agent.client.max_retries == 10
    assert agent.client.base_delay == 2.0


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
