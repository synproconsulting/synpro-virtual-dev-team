"""
Unit tests for manager_agent_router.py
"""

import pytest
import asyncio
import base64
from unittest.mock import patch, AsyncMock, MagicMock, Mock
from fastapi.testclient import TestClient
from fastapi import FastAPI
import httpx

# Import the module under test
from manager_agent_router import (
    router,
    TransitionStatus,
    TransitionResult,
    _jira_headers,
    _get_transitions,
    _post_transition,
    _get_issue_status,
    _transition_with_retry,
    _transition_by_name,
    _to_response,
    MAX_RETRIES,
    BASE_DELAY,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables for Jira."""
    monkeypatch.setenv("JIRA_BASE_URL", "https://test.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "test@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "test-token-123")


@pytest.fixture
def app():
    """Create FastAPI app with router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app, mock_env):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_transitions():
    """Sample Jira transitions response."""
    return [
        {
            "id": "11",
            "name": "Start Progress",
            "to": {"name": "In Progress", "id": "3"},
        },
        {
            "id": "21",
            "name": "Close Issue",
            "to": {"name": "Done", "id": "4"},
        },
        {
            "id": "31",
            "name": "Send to Review",
            "to": {"name": "Code Review", "id": "5"},
        },
    ]


# ── Helper Function Tests ─────────────────────────────────────────────────────


class TestJiraHeaders:
    """Test _jira_headers function."""

    def test_jira_headers_format(self, mock_env):
        """Test that Jira headers are correctly formatted."""
        headers = _jira_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")
        assert headers["Accept"] == "application/json"
        assert headers["Content-Type"] == "application/json"

    def test_jira_headers_basic_auth(self, mock_env):
        """Test that Basic Auth credentials are correctly encoded."""
        headers = _jira_headers()
        auth_header = headers["Authorization"]
        encoded = auth_header.replace("Basic ", "")
        decoded = base64.b64decode(encoded).decode()
        
        assert decoded == "test@example.com:test-token-123"


class TestGetTransitions:
    """Test _get_transitions function."""

    @pytest.mark.asyncio
    async def test_get_transitions_success(self, mock_env, sample_transitions):
        """Test successfully fetching transitions."""
        mock_response = Mock()
        mock_response.json.return_value = {"transitions": sample_transitions}
        mock_response.raise_for_status = Mock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            result = await _get_transitions("TEST-1")
            
            assert len(result) == 3
            assert result[0]["id"] == "11"
            assert result[1]["to"]["name"] == "Done"

    @pytest.mark.asyncio
    async def test_get_transitions_http_error(self, mock_env):
        """Test handling HTTP errors when fetching transitions."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404", request=Mock(), response=Mock()
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            with pytest.raises(httpx.HTTPStatusError):
                await _get_transitions("TEST-999")


class TestPostTransition:
    """Test _post_transition function."""

    @pytest.mark.asyncio
    async def test_post_transition_success(self, mock_env):
        """Test successfully posting a transition."""
        mock_response = Mock()
        mock_response.status_code = 204
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            result = await _post_transition("TEST-1", "11")
            
            assert result is True

    @pytest.mark.asyncio
    async def test_post_transition_with_comment(self, mock_env):
        """Test posting a transition with a comment."""
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            result = await _post_transition("TEST-1", "11", comment="Starting work")
            
            assert result is True
            # Verify comment was included in request body
            call_args = mock_post.call_args
            body = call_args.kwargs["json"]
            assert "update" in body
            assert "comment" in body["update"]

    @pytest.mark.asyncio
    async def test_post_transition_failure(self, mock_env):
        """Test handling failed transition post."""
        mock_response = Mock()
        mock_response.status_code = 400
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            result = await _post_transition("TEST-1", "11")
            
            assert result is False


class TestGetIssueStatus:
    """Test _get_issue_status function."""

    @pytest.mark.asyncio
    async def test_get_issue_status_success(self, mock_env):
        """Test successfully getting issue status."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "fields": {"status": {"name": "In Progress"}}
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            result = await _get_issue_status("TEST-1")
            
            assert result == "In Progress"

    @pytest.mark.asyncio
    async def test_get_issue_status_not_found(self, mock_env):
        """Test handling when issue is not found."""
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            result = await _get_issue_status("TEST-999")
            
            assert result is None


class TestTransitionWithRetry:
    """Test _transition_with_retry function."""

    @pytest.mark.asyncio
    async def test_transition_with_retry_success_first_attempt(self, mock_env):
        """Test successful transition on first attempt."""
        with patch("manager_agent_router._post_transition", new_callable=AsyncMock) as mock_post, \
             patch("manager_agent_router._get_issue_status", new_callable=AsyncMock) as mock_status:
            mock_post.return_value = True
            mock_status.return_value = "In Progress"
            
            result = await _transition_with_retry(
                "TEST-1", "11", "Start Progress"
            )
            
            assert result.status == TransitionStatus.SUCCESS
            assert result.issue_key == "TEST-1"
            assert result.transition_id == "11"
            assert result.transition_name == "Start Progress"
            assert result.attempts == 1
            assert result.final_status == "In Progress"
            assert result.error_message is None

    @pytest.mark.asyncio
    async def test_transition_with_retry_success_after_retries(self, mock_env):
        """Test successful transition after some retries."""
        call_count = 0
        
        async def mock_post_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary error")
            return True
        
        with patch("manager_agent_router._post_transition", side_effect=mock_post_side_effect), \
             patch("manager_agent_router._get_issue_status", new_callable=AsyncMock) as mock_status, \
             patch("asyncio.sleep", new_callable=AsyncMock):
            mock_status.return_value = "Done"
            
            result = await _transition_with_retry(
                "TEST-1", "21", "Close Issue"
            )
            
            assert result.status == TransitionStatus.SUCCESS
            assert result.attempts == 3
            assert result.final_status == "Done"

    @pytest.mark.asyncio
    async def test_transition_with_retry_max_retries_exceeded(self, mock_env):
        """Test failure after max retries."""
        with patch("manager_agent_router._post_transition", new_callable=AsyncMock) as mock_post, \
             patch("asyncio.sleep", new_callable=AsyncMock):
            mock_post.side_effect = Exception("Persistent error")
            
            result = await _transition_with_retry(
                "TEST-1", "11", "Start Progress"
            )
            
            assert result.status == TransitionStatus.FAILED
            assert result.attempts == MAX_RETRIES
            assert result.error_message == "Persistent error"

    @pytest.mark.asyncio
    async def test_transition_with_retry_exponential_backoff(self, mock_env):
        """Test that exponential backoff is applied."""
        with patch("manager_agent_router._post_transition", new_callable=AsyncMock) as mock_post, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_post.side_effect = Exception("Error")
            
            await _transition_with_retry("TEST-1", "11", "Start Progress")
            
            # Should sleep MAX_RETRIES - 1 times
            assert mock_sleep.call_count == MAX_RETRIES - 1
            # Check exponential backoff delays
            calls = mock_sleep.call_args_list
            assert calls[0][0][0] == BASE_DELAY * (2 ** 0)  # First retry
            assert calls[1][0][0] == BASE_DELAY * (2 ** 1)  # Second retry
            assert calls[2][0][0] == BASE_DELAY * (2 ** 2)  # Third retry

    @pytest.mark.asyncio
    async def test_transition_with_retry_with_comment(self, mock_env):
        """Test transition with retry includes comment."""
        with patch("manager_agent_router._post_transition", new_callable=AsyncMock) as mock_post, \
             patch("manager_agent_router._get_issue_status", new_callable=AsyncMock) as mock_status:
            mock_post.return_value = True
            mock_status.return_value = "In Progress"
            
            await _transition_with_retry(
                "TEST-1", "11", "Start Progress", comment="Test comment"
            )
            
            mock_post.assert_called_once_with("TEST-1", "11", "Test comment")


class TestTransitionByName:
    """Test _transition_by_name function."""

    @pytest.mark.asyncio
    async def test_transition_by_name_success(self, mock_env, sample_transitions):
        """Test successful transition by status name."""
        with patch("manager_agent_router._get_transitions", new_callable=AsyncMock) as mock_get, \
             patch("manager_agent_router._transition_with_retry", new_callable=AsyncMock) as mock_retry:
            mock_get.return_value = sample_transitions
            mock_retry.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
                transition_id="11",
                transition_name="Start Progress",
                final_status="In Progress",
            )
            
            result = await _transition_by_name("TEST-1", "In Progress")
            
            assert result.status == TransitionStatus.SUCCESS
            mock_retry.assert_called_once_with("TEST-1", "11", "Start Progress", None)

    @pytest.mark.asyncio
    async def test_transition_by_name_case_insensitive(self, mock_env, sample_transitions):
        """Test that status name matching is case-insensitive."""
        with patch("manager_agent_router._get_transitions", new_callable=AsyncMock) as mock_get, \
             patch("manager_agent_router._transition_with_retry", new_callable=AsyncMock) as mock_retry:
            mock_get.return_value = sample_transitions
            mock_retry.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
            )
            
            await _transition_by_name("TEST-1", "in progress")
            
            # Should find the transition despite case difference
            mock_retry.assert_called_once()

    @pytest.mark.asyncio
    async def test_transition_by_name_not_available(self, mock_env, sample_transitions):
        """Test handling when target status is not available."""
        with patch("manager_agent_router._get_transitions", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_transitions
            
            result = await _transition_by_name("TEST-1", "Invalid Status")
            
            assert result.status == TransitionStatus.FAILED
            assert "not available" in result.error_message
            assert "In Progress" in result.error_message
            assert "Done" in result.error_message

    @pytest.mark.asyncio
    async def test_transition_by_name_fetch_error(self, mock_env):
        """Test handling error when fetching transitions."""
        with patch("manager_agent_router._get_transitions", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("API error")
            
            result = await _transition_by_name("TEST-1", "In Progress")
            
            assert result.status == TransitionStatus.FAILED
            assert "Failed to fetch transitions" in result.error_message
            assert "API error" in result.error_message

    @pytest.mark.asyncio
    async def test_transition_by_name_with_comment(self, mock_env, sample_transitions):
        """Test transition by name with comment."""
        with patch("manager_agent_router._get_transitions", new_callable=AsyncMock) as mock_get, \
             patch("manager_agent_router._transition_with_retry", new_callable=AsyncMock) as mock_retry:
            mock_get.return_value = sample_transitions
            mock_retry.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
            )
            
            await _transition_by_name("TEST-1", "Done", comment="Finished work")
            
            mock_retry.assert_called_once_with(
                "TEST-1", "21", "Close Issue", "Finished work"
            )


class TestToResponse:
    """Test _to_response function."""

    def test_to_response_success(self):
        """Test converting successful result to response."""
        result = TransitionResult(
            issue_key="TEST-1",
            status=TransitionStatus.SUCCESS,
            attempts=1,
            total_time=0.5,
            transition_id="11",
            transition_name="Start Progress",
            final_status="In Progress",
        )
        
        response = _to_response(result)
        
        assert response.success is True
        assert response.status == "success"
        assert response.issue_key == "TEST-1"
        assert response.transition_id == "11"
        assert response.transition_name == "Start Progress"
        assert response.attempts == 1
        assert response.total_time == 0.5
        assert response.final_status == "In Progress"
        assert response.error_message is None

    def test_to_response_failed(self):
        """Test converting failed result to response."""
        result = TransitionResult(
            issue_key="TEST-1",
            status=TransitionStatus.FAILED,
            attempts=4,
            total_time=15.0,
            error_message="Max retries exceeded",
        )
        
        response = _to_response(result)
        
        assert response.success is False
        assert response.status == "failed"
        assert response.error_message == "Max retries exceeded"
        assert response.attempts == 4


# ── Router Endpoint Tests ─────────────────────────────────────────────────────


class TestTransitionEndpoint:
    """Test /api/manager-agent/transition endpoint."""

    def test_transition_by_target_status(self, client):
        """Test transition endpoint with target_status."""
        with patch("manager_agent_router._transition_by_name", new_callable=AsyncMock) as mock_transition:
            mock_transition.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
                transition_name="Start Progress",
                final_status="In Progress",
            )
            
            response = client.post(
                "/api/manager-agent/transition",
                json={
                    "issue_key": "TEST-1",
                    "target_status": "In Progress",
                    "comment": "Starting work",
                },
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["issue_key"] == "TEST-1"
            assert data["final_status"] == "In Progress"
            
            mock_transition.assert_called_once_with(
                "TEST-1", "In Progress", comment="Starting work"
            )

    def test_transition_by_transition_id(self, client):
        """Test transition endpoint with transition_id."""
        with patch("manager_agent_router._transition_with_retry", new_callable=AsyncMock) as mock_transition:
            mock_transition.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
                transition_id="11",
            )
            
            response = client.post(
                "/api/manager-agent/transition",
                json={"issue_key": "TEST-1", "transition_id": "11"},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["transition_id"] == "11"

    def test_transition_missing_both_params(self, client):
        """Test transition endpoint without target_status or transition_id."""
        response = client.post(
            "/api/manager-agent/transition",
            json={"issue_key": "TEST-1"},
        )
        
        assert response.status_code == 400
        assert "target_status or transition_id must be provided" in response.json()["detail"]

    def test_transition_failed_result(self, client):
        """Test transition endpoint returning failed result."""
        with patch("manager_agent_router._transition_by_name", new_callable=AsyncMock) as mock_transition:
            mock_transition.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.FAILED,
                attempts=4,
                total_time=15.0,
                error_message="Status not available",
            )
            
            response = client.post(
                "/api/manager-agent/transition",
                json={"issue_key": "TEST-1", "target_status": "Invalid"},
            )
            
            assert response.status_code == 200  # Returns 200 but success=False
            data = response.json()
            assert data["success"] is False
            assert data["status"] == "failed"
            assert "Status not available" in data["error_message"]


class TestBulkTransitionEndpoint:
    """Test /api/manager-agent/bulk-transition endpoint."""

    def test_bulk_transition_all_success(self, client):
        """Test bulk transition with all successful transitions."""
        with patch("manager_agent_router._transition_by_name", new_callable=AsyncMock) as mock_by_name, \
             patch("manager_agent_router._transition_with_retry", new_callable=AsyncMock) as mock_with_retry:
            
            mock_by_name.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
            )
            mock_with_retry.return_value = TransitionResult(
                issue_key="TEST-2",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
            )
            
            response = client.post(
                "/api/manager-agent/bulk-transition",
                json={
                    "transitions": [
                        {"issue_key": "TEST-1", "target_status": "In Progress"},
                        {"issue_key": "TEST-2", "transition_id": "11"},
                    ]
                },
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert data["successful"] == 2
            assert data["failed"] == 0
            assert len(data["results"]) == 2

    def test_bulk_transition_mixed_results(self, client):
        """Test bulk transition with mixed success and failure."""
        results = [
            TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
            ),
            TransitionResult(
                issue_key="TEST-2",
                status=TransitionStatus.FAILED,
                attempts=4,
                total_time=15.0,
                error_message="Error",
            ),
        ]
        
        call_count = 0
        
        async def mock_transition(*args, **kwargs):
            nonlocal call_count
            result = results[call_count]
            call_count += 1
            return result
        
        with patch("manager_agent_router._transition_by_name", side_effect=mock_transition):
            response = client.post(
                "/api/manager-agent/bulk-transition",
                json={
                    "transitions": [
                        {"issue_key": "TEST-1", "target_status": "In Progress"},
                        {"issue_key": "TEST-2", "target_status": "Invalid"},
                    ]
                },
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert data["successful"] == 1
            assert data["failed"] == 1

    def test_bulk_transition_invalid_request(self, client):
        """Test bulk transition with invalid request (missing both params)."""
        response = client.post(
            "/api/manager-agent/bulk-transition",
            json={
                "transitions": [
                    {"issue_key": "TEST-1"},  # Missing both target_status and transition_id
                ]
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["failed"] == 1
        assert "required" in data["results"][0]["error_message"]

    def test_bulk_transition_empty_list(self, client):
        """Test bulk transition with empty transitions list."""
        response = client.post(
            "/api/manager-agent/bulk-transition",
            json={"transitions": []},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["successful"] == 0
        assert data["failed"] == 0


class TestStartWorkEndpoint:
    """Test /api/manager-agent/start-work/{issue_key} endpoint."""

    def test_start_work_success(self, client):
        """Test start work endpoint."""
        with patch("manager_agent_router._transition_by_name", new_callable=AsyncMock) as mock_transition:
            mock_transition.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
                final_status="In Progress",
            )
            
            response = client.post("/api/manager-agent/start-work/TEST-1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["final_status"] == "In Progress"
            
            mock_transition.assert_called_once_with("TEST-1", "In Progress", None)

    def test_start_work_with_comment(self, client):
        """Test start work endpoint with comment."""
        with patch("manager_agent_router._transition_by_name", new_callable=AsyncMock) as mock_transition:
            mock_transition.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
            )
            
            response = client.post(
                "/api/manager-agent/start-work/TEST-1",
                params={"comment": "Starting now"},
            )
            
            assert response.status_code == 200
            mock_transition.assert_called_once_with("TEST-1", "In Progress", "Starting now")


class TestCompleteWorkEndpoint:
    """Test /api/manager-agent/complete-work/{issue_key} endpoint."""

    def test_complete_work_success(self, client):
        """Test complete work endpoint."""
        with patch("manager_agent_router._transition_by_name", new_callable=AsyncMock) as mock_transition:
            mock_transition.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
                final_status="Done",
            )
            
            response = client.post("/api/manager-agent/complete-work/TEST-1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["final_status"] == "Done"
            
            mock_transition.assert_called_once_with("TEST-1", "Done", None)


class TestCodeReviewEndpoint:
    """Test /api/manager-agent/code-review/{issue_key} endpoint."""

    def test_move_to_code_review_success(self, client):
        """Test code review endpoint."""
        with patch("manager_agent_router._transition_by_name", new_callable=AsyncMock) as mock_transition:
            mock_transition.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
                final_status="Code Review",
            )
            
            response = client.post("/api/manager-agent/code-review/TEST-1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["final_status"] == "Code Review"
            
            mock_transition.assert_called_once_with("TEST-1", "Code Review", None)


class TestTestingEndpoint:
    """Test /api/manager-agent/testing/{issue_key} endpoint."""

    def test_move_to_testing_success(self, client):
        """Test testing endpoint."""
        with patch("manager_agent_router._transition_by_name", new_callable=AsyncMock) as mock_transition:
            mock_transition.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
                final_status="Testing",
            )
            
            response = client.post("/api/manager-agent/testing/TEST-1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["final_status"] == "Testing"
            
            mock_transition.assert_called_once_with("TEST-1", "Testing", None)


class TestGetIssueStatusEndpoint:
    """Test /api/manager-agent/status/{issue_key} endpoint."""

    def test_get_status_success(self, client):
        """Test get issue status endpoint."""
        with patch("manager_agent_router._get_issue_status", new_callable=AsyncMock) as mock_status:
            mock_status.return_value = "In Progress"
            
            response = client.get("/api/manager-agent/status/TEST-1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["issue_key"] == "TEST-1"
            assert data["status"] == "In Progress"

    def test_get_status_not_found(self, client):
        """Test get issue status when issue not found."""
        with patch("manager_agent_router._get_issue_status", new_callable=AsyncMock) as mock_status:
            mock_status.return_value = None
            
            response = client.get("/api/manager-agent/status/TEST-999")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]


# ── Integration Tests ─────────────────────────────────────────────────────────


class TestIntegration:
    """Integration tests for the full flow."""

    @pytest.mark.asyncio
    async def test_full_transition_flow(self, mock_env, sample_transitions):
        """Test complete flow from fetching transitions to completing transition."""
        # Mock all HTTP calls
        mock_get_response = Mock()
        mock_get_response.json.return_value = {"transitions": sample_transitions}
        mock_get_response.raise_for_status = Mock()
        mock_get_response.status_code = 200
        
        mock_post_response = Mock()
        mock_post_response.status_code = 204
        
        mock_status_response = Mock()
        mock_status_response.status_code = 200
        mock_status_response.json.return_value = {
            "fields": {"status": {"name": "In Progress"}}
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            async_client = mock_client.return_value.__aenter__.return_value
            
            # Setup mock responses for each call
            async_client.get = AsyncMock()
            async_client.post = AsyncMock(return_value=mock_post_response)
            
            # First call returns transitions, second returns status
            async_client.get.side_effect = [mock_get_response, mock_status_response]
            
            # Execute the full flow
            result = await _transition_by_name("TEST-1", "In Progress", "Starting work")
            
            assert result.status == TransitionStatus.SUCCESS
            assert result.final_status == "In Progress"
            assert result.attempts == 1

    def test_end_to_end_api_call(self, client, sample_transitions):
        """Test end-to-end API call through the router."""
        mock_get_response = Mock()
        mock_get_response.json.return_value = {"transitions": sample_transitions}
        mock_get_response.raise_for_status = Mock()
        mock_get_response.status_code = 200
        
        mock_post_response = Mock()
        mock_post_response.status_code = 204
        
        mock_status_response = Mock()
        mock_status_response.status_code = 200
        mock_status_response.json.return_value = {
            "fields": {"status": {"name": "Done"}}
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            async_client = mock_client.return_value.__aenter__.return_value
            async_client.get = AsyncMock()
            async_client.post = AsyncMock(return_value=mock_post_response)
            async_client.get.side_effect = [mock_get_response, mock_status_response]
            
            response = client.post(
                "/api/manager-agent/complete-work/TEST-1",
                params={"comment": "Work completed"},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["issue_key"] == "TEST-1"
            assert data["final_status"] == "Done"
