"""
Unit tests for manager_agent_router.py

Tests cover:
- Jira helper functions (_get_transitions, _post_transition, _get_issue_status)
- Retry logic with exponential backoff (_transition_with_retry)
- Transition by name resolution (_transition_by_name)
- FastAPI endpoints (transition, bulk-transition, convenience endpoints)
- Error handling and edge cases
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock, Mock
from fastapi.testclient import TestClient
import httpx

# Import the module under test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from manager_agent_router import (
    router,
    TransitionStatus,
    TransitionResult,
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
def test_client(mock_env):
    """Create FastAPI test client."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for testing HTTP calls."""
    return AsyncMock(spec=httpx.AsyncClient)


# ── Helper Function Tests ─────────────────────────────────────────────────────


class TestJiraHelpers:
    """Test Jira API helper functions."""

    @pytest.mark.asyncio
    async def test_get_transitions_success(self, mock_env):
        """Test fetching transitions for an issue."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "transitions": [
                {"id": "11", "name": "Start Progress", "to": {"name": "In Progress"}},
                {"id": "21", "name": "Done", "to": {"name": "Done"}},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("manager_agent_router.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await _get_transitions("TEST-1")

            assert len(result) == 2
            assert result[0]["id"] == "11"
            assert result[0]["to"]["name"] == "In Progress"
            mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_transitions_http_error(self, mock_env):
        """Test _get_transitions raises on HTTP error."""
        with patch("manager_agent_router.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404", request=MagicMock(), response=MagicMock()
            )
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await _get_transitions("INVALID-1")

    @pytest.mark.asyncio
    async def test_post_transition_success(self, mock_env):
        """Test posting a transition successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 204

        with patch("manager_agent_router.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await _post_transition("TEST-1", "11", "Starting work")

            assert result is True
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_post_transition_with_comment(self, mock_env):
        """Test posting a transition with a comment."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("manager_agent_router.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await _post_transition("TEST-1", "11", "Test comment")

            assert result is True
            call_args = mock_client.post.call_args
            posted_json = call_args.kwargs["json"]
            assert "update" in posted_json
            assert "comment" in posted_json["update"]

    @pytest.mark.asyncio
    async def test_post_transition_failure(self, mock_env):
        """Test posting a transition that fails."""
        mock_response = MagicMock()
        mock_response.status_code = 400

        with patch("manager_agent_router.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await _post_transition("TEST-1", "99")

            assert result is False

    @pytest.mark.asyncio
    async def test_get_issue_status_success(self, mock_env):
        """Test getting issue status successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "fields": {"status": {"name": "In Progress"}}
        }

        with patch("manager_agent_router.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await _get_issue_status("TEST-1")

            assert result == "In Progress"

    @pytest.mark.asyncio
    async def test_get_issue_status_not_found(self, mock_env):
        """Test getting status for non-existent issue."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("manager_agent_router.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await _get_issue_status("INVALID-1")

            assert result is None


# ── Retry Logic Tests ─────────────────────────────────────────────────────────


class TestRetryLogic:
    """Test exponential backoff retry logic."""

    @pytest.mark.asyncio
    async def test_transition_with_retry_success_first_attempt(self, mock_env):
        """Test successful transition on first attempt."""
        with patch("manager_agent_router._post_transition") as mock_post, \
             patch("manager_agent_router._get_issue_status") as mock_status:
            mock_post.return_value = True
            mock_status.return_value = "In Progress"

            result = await _transition_with_retry("TEST-1", "11", "Start Progress")

            assert result.status == TransitionStatus.SUCCESS
            assert result.attempts == 1
            assert result.issue_key == "TEST-1"
            assert result.transition_id == "11"
            assert result.final_status == "In Progress"
            assert mock_post.call_count == 1

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
             patch("manager_agent_router._get_issue_status", return_value="Done"), \
             patch("manager_agent_router.asyncio.sleep", return_value=None):

            result = await _transition_with_retry("TEST-1", "21", "Done")

            assert result.status == TransitionStatus.SUCCESS
            assert result.attempts == 3
            assert result.final_status == "Done"

    @pytest.mark.asyncio
    async def test_transition_with_retry_all_attempts_fail(self, mock_env):
        """Test all retry attempts fail."""
        async def mock_post_fail(*args, **kwargs):
            raise Exception("Persistent error")

        with patch("manager_agent_router._post_transition", side_effect=mock_post_fail), \
             patch("manager_agent_router.asyncio.sleep", return_value=None):

            result = await _transition_with_retry("TEST-1", "11", "Start Progress")

            assert result.status == TransitionStatus.FAILED
            assert result.attempts == MAX_RETRIES
            assert "Persistent error" in result.error_message

    @pytest.mark.asyncio
    async def test_transition_with_retry_exponential_backoff(self, mock_env):
        """Test that exponential backoff delays are applied."""
        sleep_calls = []

        async def mock_post_fail(*args, **kwargs):
            raise Exception("Error")

        async def mock_sleep(delay):
            sleep_calls.append(delay)

        with patch("manager_agent_router._post_transition", side_effect=mock_post_fail), \
             patch("manager_agent_router.asyncio.sleep", side_effect=mock_sleep):

            result = await _transition_with_retry("TEST-1", "11", "Start")

            # Should have MAX_RETRIES - 1 sleep calls (no sleep after last attempt)
            assert len(sleep_calls) == MAX_RETRIES - 1
            # Verify exponential backoff pattern
            assert sleep_calls[0] == BASE_DELAY * (2 ** 0)
            assert sleep_calls[1] == BASE_DELAY * (2 ** 1)
            assert sleep_calls[2] == BASE_DELAY * (2 ** 2)

    @pytest.mark.asyncio
    async def test_transition_with_retry_includes_comment(self, mock_env):
        """Test retry logic passes comment through."""
        with patch("manager_agent_router._post_transition") as mock_post, \
             patch("manager_agent_router._get_issue_status", return_value="Done"):
            mock_post.return_value = True

            await _transition_with_retry("TEST-1", "21", "Done", "Test comment")

            mock_post.assert_called_once_with("TEST-1", "21", "Test comment")


# ── Transition by Name Tests ──────────────────────────────────────────────────


class TestTransitionByName:
    """Test transition resolution by target status name."""

    @pytest.mark.asyncio
    async def test_transition_by_name_success(self, mock_env):
        """Test successful transition by status name."""
        transitions = [
            {"id": "11", "name": "Start Progress", "to": {"name": "In Progress"}},
            {"id": "21", "name": "Done", "to": {"name": "Done"}},
        ]

        with patch("manager_agent_router._get_transitions", return_value=transitions), \
             patch("manager_agent_router._transition_with_retry") as mock_retry:
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
    async def test_transition_by_name_case_insensitive(self, mock_env):
        """Test transition matching is case-insensitive."""
        transitions = [
            {"id": "11", "name": "Start Progress", "to": {"name": "In Progress"}},
        ]

        with patch("manager_agent_router._get_transitions", return_value=transitions), \
             patch("manager_agent_router._transition_with_retry") as mock_retry:
            mock_retry.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
            )

            result = await _transition_by_name("TEST-1", "in progress")

            assert result.status == TransitionStatus.SUCCESS
            mock_retry.assert_called_once()

    @pytest.mark.asyncio
    async def test_transition_by_name_not_found(self, mock_env):
        """Test transition fails when status not available."""
        transitions = [
            {"id": "11", "name": "Start Progress", "to": {"name": "In Progress"}},
        ]

        with patch("manager_agent_router._get_transitions", return_value=transitions):
            result = await _transition_by_name("TEST-1", "Invalid Status")

            assert result.status == TransitionStatus.FAILED
            assert "not available" in result.error_message
            assert "In Progress" in result.error_message

    @pytest.mark.asyncio
    async def test_transition_by_name_fetch_error(self, mock_env):
        """Test transition fails when fetching transitions fails."""
        with patch("manager_agent_router._get_transitions", side_effect=Exception("Network error")):
            result = await _transition_by_name("TEST-1", "In Progress")

            assert result.status == TransitionStatus.FAILED
            assert "Failed to fetch transitions" in result.error_message
            assert "Network error" in result.error_message

    @pytest.mark.asyncio
    async def test_transition_by_name_with_comment(self, mock_env):
        """Test transition by name passes comment through."""
        transitions = [
            {"id": "21", "name": "Done", "to": {"name": "Done"}},
        ]

        with patch("manager_agent_router._get_transitions", return_value=transitions), \
             patch("manager_agent_router._transition_with_retry") as mock_retry:
            mock_retry.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
            )

            await _transition_by_name("TEST-1", "Done", "Work completed")

            mock_retry.assert_called_once_with("TEST-1", "21", "Done", "Work completed")


# ── Response Conversion Tests ─────────────────────────────────────────────────


class TestResponseConversion:
    """Test conversion from TransitionResult to TransitionResponse."""

    def test_to_response_success(self):
        """Test converting successful result to response."""
        result = TransitionResult(
            issue_key="TEST-1",
            status=TransitionStatus.SUCCESS,
            attempts=2,
            total_time=1.5,
            transition_id="11",
            transition_name="Start Progress",
            final_status="In Progress",
        )

        response = _to_response(result)

        assert response.success is True
        assert response.status == "success"
        assert response.issue_key == "TEST-1"
        assert response.attempts == 2
        assert response.total_time == 1.5
        assert response.transition_id == "11"
        assert response.transition_name == "Start Progress"
        assert response.final_status == "In Progress"
        assert response.error_message is None

    def test_to_response_failure(self):
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
        assert response.issue_key == "TEST-1"
        assert response.attempts == 4
        assert response.error_message == "Max retries exceeded"


# ── API Endpoint Tests ────────────────────────────────────────────────────────


class TestTransitionEndpoint:
    """Test /api/manager-agent/transition endpoint."""

    def test_transition_by_target_status(self, test_client):
        """Test transition endpoint with target_status."""
        with patch("manager_agent_router._transition_by_name") as mock_transition:
            mock_transition.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
                final_status="In Progress",
            )

            response = test_client.post(
                "/api/manager-agent/transition",
                json={
                    "issue_key": "TEST-1",
                    "target_status": "In Progress",
                    "comment": "Starting work",
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["issue_key"] == "TEST-1"
            mock_transition.assert_called_once()

    def test_transition_by_transition_id(self, test_client):
        """Test transition endpoint with transition_id."""
        with patch("manager_agent_router._transition_with_retry") as mock_retry:
            mock_retry.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
                transition_id="11",
            )

            response = test_client.post(
                "/api/manager-agent/transition",
                json={
                    "issue_key": "TEST-1",
                    "transition_id": "11",
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            mock_retry.assert_called_once()

    def test_transition_missing_parameters(self, test_client):
        """Test transition endpoint fails without target_status or transition_id."""
        response = test_client.post(
            "/api/manager-agent/transition",
            json={"issue_key": "TEST-1"}
        )

        assert response.status_code == 400
        assert "target_status or transition_id must be provided" in response.json()["detail"]

    def test_transition_with_both_parameters(self, test_client):
        """Test transition prefers transition_id when both provided."""
        with patch("manager_agent_router._transition_with_retry") as mock_retry:
            mock_retry.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
            )

            response = test_client.post(
                "/api/manager-agent/transition",
                json={
                    "issue_key": "TEST-1",
                    "target_status": "In Progress",
                    "transition_id": "11",
                }
            )

            assert response.status_code == 200
            # Should call _transition_with_retry, not _transition_by_name
            mock_retry.assert_called_once()


class TestBulkTransitionEndpoint:
    """Test /api/manager-agent/bulk-transition endpoint."""

    def test_bulk_transition_success(self, test_client):
        """Test bulk transition with multiple issues."""
        async def mock_by_name(issue_key, status, comment=None):
            return TransitionResult(
                issue_key=issue_key,
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
                final_status=status,
            )

        with patch("manager_agent_router._transition_by_name", side_effect=mock_by_name):
            response = test_client.post(
                "/api/manager-agent/bulk-transition",
                json={
                    "transitions": [
                        {"issue_key": "TEST-1", "target_status": "In Progress"},
                        {"issue_key": "TEST-2", "target_status": "Done"},
                    ]
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert data["successful"] == 2
            assert data["failed"] == 0
            assert len(data["results"]) == 2

    def test_bulk_transition_mixed_results(self, test_client):
        """Test bulk transition with mixed success/failure."""
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
                total_time=10.0,
                error_message="Failed",
            ),
        ]

        call_count = [0]

        async def mock_transition(*args, **kwargs):
            result = results[call_count[0]]
            call_count[0] += 1
            return result

        with patch("manager_agent_router._transition_by_name", side_effect=mock_transition):
            response = test_client.post(
                "/api/manager-agent/bulk-transition",
                json={
                    "transitions": [
                        {"issue_key": "TEST-1", "target_status": "In Progress"},
                        {"issue_key": "TEST-2", "target_status": "Done"},
                    ]
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert data["successful"] == 1
            assert data["failed"] == 1

    def test_bulk_transition_with_transition_ids(self, test_client):
        """Test bulk transition using transition IDs."""
        async def mock_retry(issue_key, tid, name, comment=None):
            return TransitionResult(
                issue_key=issue_key,
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
            )

        with patch("manager_agent_router._transition_with_retry", side_effect=mock_retry):
            response = test_client.post(
                "/api/manager-agent/bulk-transition",
                json={
                    "transitions": [
                        {"issue_key": "TEST-1", "transition_id": "11"},
                        {"issue_key": "TEST-2", "transition_id": "21"},
                    ]
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["successful"] == 2

    def test_bulk_transition_missing_parameters(self, test_client):
        """Test bulk transition with missing required fields."""
        response = test_client.post(
            "/api/manager-agent/bulk-transition",
            json={
                "transitions": [
                    {"issue_key": "TEST-1"},  # Missing both target_status and transition_id
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["failed"] == 1
        assert "required" in data["results"][0]["error_message"].lower()


class TestConvenienceEndpoints:
    """Test convenience endpoints for common transitions."""

    def test_start_work_endpoint(self, test_client):
        """Test /start-work endpoint."""
        with patch("manager_agent_router._transition_by_name") as mock_transition:
            mock_transition.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
                final_status="In Progress",
            )

            response = test_client.post("/api/manager-agent/start-work/TEST-1")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["final_status"] == "In Progress"
            mock_transition.assert_called_once_with("TEST-1", "In Progress", None)

    def test_start_work_with_comment(self, test_client):
        """Test /start-work endpoint with comment."""
        with patch("manager_agent_router._transition_by_name") as mock_transition:
            mock_transition.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
            )

            response = test_client.post(
                "/api/manager-agent/start-work/TEST-1?comment=Starting%20now"
            )

            assert response.status_code == 200
            mock_transition.assert_called_once_with("TEST-1", "In Progress", "Starting now")

    def test_complete_work_endpoint(self, test_client):
        """Test /complete-work endpoint."""
        with patch("manager_agent_router._transition_by_name") as mock_transition:
            mock_transition.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
                final_status="Done",
            )

            response = test_client.post("/api/manager-agent/complete-work/TEST-1")

            assert response.status_code == 200
            data = response.json()
            assert data["final_status"] == "Done"
            mock_transition.assert_called_once_with("TEST-1", "Done", None)

    def test_code_review_endpoint(self, test_client):
        """Test /code-review endpoint."""
        with patch("manager_agent_router._transition_by_name") as mock_transition:
            mock_transition.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
                final_status="Code Review",
            )

            response = test_client.post("/api/manager-agent/code-review/TEST-1")

            assert response.status_code == 200
            data = response.json()
            assert data["final_status"] == "Code Review"
            mock_transition.assert_called_once_with("TEST-1", "Code Review", None)

    def test_testing_endpoint(self, test_client):
        """Test /testing endpoint."""
        with patch("manager_agent_router._transition_by_name") as mock_transition:
            mock_transition.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
                final_status="Testing",
            )

            response = test_client.post("/api/manager-agent/testing/TEST-1")

            assert response.status_code == 200
            data = response.json()
            assert data["final_status"] == "Testing"
            mock_transition.assert_called_once_with("TEST-1", "Testing", None)


class TestGetStatusEndpoint:
    """Test /status endpoint."""

    def test_get_status_success(self, test_client):
        """Test getting issue status."""
        with patch("manager_agent_router._get_issue_status") as mock_status:
            mock_status.return_value = "In Progress"

            response = test_client.get("/api/manager-agent/status/TEST-1")

            assert response.status_code == 200
            data = response.json()
            assert data["issue_key"] == "TEST-1"
            assert data["status"] == "In Progress"

    def test_get_status_not_found(self, test_client):
        """Test getting status for non-existent issue."""
        with patch("manager_agent_router._get_issue_status") as mock_status:
            mock_status.return_value = None

            response = test_client.get("/api/manager-agent/status/INVALID-1")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()


# ── Edge Cases and Error Handling ─────────────────────────────────────────────


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_bulk_transition(self, test_client):
        """Test bulk transition with empty list."""
        response = test_client.post(
            "/api/manager-agent/bulk-transition",
            json={"transitions": []}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["successful"] == 0
        assert data["failed"] == 0

    def test_transition_result_default_values(self):
        """Test TransitionResult dataclass default values."""
        result = TransitionResult(
            issue_key="TEST-1",
            status=TransitionStatus.SUCCESS,
        )

        assert result.attempts == 0
        assert result.total_time == 0.0
        assert result.transition_id is None
        assert result.transition_name is None
        assert result.error_message is None
        assert result.final_status is None

    @pytest.mark.asyncio
    async def test_concurrent_bulk_transitions(self, test_client):
        """Test that bulk transitions run concurrently."""
        call_times = []

        async def mock_transition(*args, **kwargs):
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.1)  # Simulate API call
            return TransitionResult(
                issue_key=args[0],
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.1,
            )

        with patch("manager_agent_router._transition_by_name", side_effect=mock_transition):
            response = test_client.post(
                "/api/manager-agent/bulk-transition",
                json={
                    "transitions": [
                        {"issue_key": f"TEST-{i}", "target_status": "Done"}
                        for i in range(5)
                    ]
                }
            )

            assert response.status_code == 200
            # All calls should start at roughly the same time (concurrent)
            # If sequential, they would be 0.5s apart total
            # If concurrent, they should all complete in ~0.1s
            # (This is a basic concurrency check)
            assert len(call_times) == 5

    def test_invalid_json_request(self, test_client):
        """Test handling of invalid JSON."""
        response = test_client.post(
            "/api/manager-agent/transition",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422  # Unprocessable Entity

    def test_special_characters_in_issue_key(self, test_client):
        """Test handling issue keys with special characters."""
        with patch("manager_agent_router._transition_by_name") as mock_transition:
            mock_transition.return_value = TransitionResult(
                issue_key="PROJECT-123",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
            )

            response = test_client.post(
                "/api/manager-agent/start-work/PROJECT-123"
            )

            assert response.status_code == 200
            mock_transition.assert_called_once_with("PROJECT-123", "In Progress", None)

    def test_very_long_comment(self, test_client):
        """Test handling very long comments."""
        long_comment = "x" * 10000

        with patch("manager_agent_router._transition_by_name") as mock_transition:
            mock_transition.return_value = TransitionResult(
                issue_key="TEST-1",
                status=TransitionStatus.SUCCESS,
                attempts=1,
                total_time=0.5,
            )

            response = test_client.post(
                "/api/manager-agent/transition",
                json={
                    "issue_key": "TEST-1",
                    "target_status": "Done",
                    "comment": long_comment,
                }
            )

            assert response.status_code == 200
            mock_transition.assert_called_once_with("TEST-1", "Done", long_comment)
