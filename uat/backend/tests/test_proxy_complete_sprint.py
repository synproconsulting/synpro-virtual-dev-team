"""
Unit tests for the /proxy/jira/sprint/{sprint_id}/complete endpoint.

Verifies:
- POST (partial update) is used to close the sprint — not PUT (full update)
- Successful close returns success=True with incompleteMoved count
- Failure returns success=False with a meaningful error field (not "Unknown error")
- Incomplete tickets are moved to backlog when moveIncompleteTo=="backlog"
- Incomplete tickets are moved to the next sprint when moveIncompleteTo=="nextSprint"
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from proxy import router


# proxy.py reads env vars at import time into module-level globals.
# Tests must patch those globals directly, not monkeypatch the env.
PATCH_BASE_URL = "proxy.JIRA_BASE_URL"


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _mock_response(status_code, json_body=None):
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = json_body or {}
    return r


class TestCompleteSprintUsesPost:
    """The sprint-close call must use POST, not PUT."""

    def test_post_used_to_close_sprint(self, client):
        with patch(PATCH_BASE_URL, "https://test.atlassian.net"), \
             patch("proxy.httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_cls.return_value.__aenter__.return_value = mock_http
            mock_http.get.return_value = _mock_response(200, {"issues": []})
            mock_http.post.return_value = _mock_response(200, {
                "id": 171, "state": "closed", "name": "SDT1 Sprint 8"
            })

            resp = client.post(
                "/proxy/jira/sprint/171/complete",
                json={"moveIncompleteTo": "backlog"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert mock_http.post.called
        assert mock_http.put.call_count == 0, "PUT must not be used for sprint close"
        # Verify the POST was to the sprint endpoint
        post_call_urls = [str(c) for c in mock_http.post.call_args_list]
        assert any("sprint/171" in u for u in post_call_urls)


class TestCompleteSprintSuccess:
    """Endpoint returns success=True when Jira returns 200."""

    def test_no_incomplete_tickets(self, client):
        with patch(PATCH_BASE_URL, "https://test.atlassian.net"), \
             patch("proxy.httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_cls.return_value.__aenter__.return_value = mock_http
            mock_http.get.return_value = _mock_response(200, {"issues": []})
            mock_http.post.return_value = _mock_response(200, {"state": "closed"})

            resp = client.post(
                "/proxy/jira/sprint/171/complete",
                json={"moveIncompleteTo": "backlog"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["incompleteMoved"] == 0
        assert "error" not in data

    def test_incomplete_tickets_moved_to_backlog(self, client):
        incomplete_issues = [{"key": "TEST-1"}, {"key": "TEST-2"}]
        with patch(PATCH_BASE_URL, "https://test.atlassian.net"), \
             patch("proxy.httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_cls.return_value.__aenter__.return_value = mock_http
            mock_http.get.return_value = _mock_response(200, {"issues": incomplete_issues})
            mock_http.post.return_value = _mock_response(200, {"state": "closed"})

            resp = client.post(
                "/proxy/jira/sprint/171/complete",
                json={"moveIncompleteTo": "backlog"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["incompleteMoved"] == 2
        post_call_urls = [str(c) for c in mock_http.post.call_args_list]
        assert any("backlog/issue" in u for u in post_call_urls)

    def test_incomplete_tickets_moved_to_next_sprint(self, client):
        incomplete_issues = [{"key": "TEST-3"}]
        with patch(PATCH_BASE_URL, "https://test.atlassian.net"), \
             patch("proxy.httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_cls.return_value.__aenter__.return_value = mock_http
            mock_http.get.return_value = _mock_response(200, {"issues": incomplete_issues})
            mock_http.post.return_value = _mock_response(200, {"state": "closed"})

            resp = client.post(
                "/proxy/jira/sprint/171/complete",
                json={"moveIncompleteTo": "nextSprint", "nextSprintId": "172"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["incompleteMoved"] == 1
        post_call_urls = [str(c) for c in mock_http.post.call_args_list]
        assert any("sprint/172/issue" in u for u in post_call_urls)


class TestCompleteSprintFailure:
    """Endpoint returns meaningful error messages on failure."""

    def test_jira_400_returns_field_error(self, client):
        with patch(PATCH_BASE_URL, "https://test.atlassian.net"), \
             patch("proxy.httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_cls.return_value.__aenter__.return_value = mock_http
            mock_http.get.return_value = _mock_response(200, {"issues": []})
            mock_http.post.return_value = _mock_response(
                400,
                {"errorMessages": [], "errors": {"name": "Sprint name is required"}}
            )

            resp = client.post(
                "/proxy/jira/sprint/171/complete",
                json={"moveIncompleteTo": "backlog"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "error" in data
        assert data["error"] != "Unknown error"
        assert "Sprint name is required" in data["error"]

    def test_jira_error_messages_field(self, client):
        with patch(PATCH_BASE_URL, "https://test.atlassian.net"), \
             patch("proxy.httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_cls.return_value.__aenter__.return_value = mock_http
            mock_http.get.return_value = _mock_response(200, {"issues": []})
            mock_http.post.return_value = _mock_response(
                403,
                {"errorMessages": ["User does not have permission"], "errors": {}}
            )

            resp = client.post(
                "/proxy/jira/sprint/171/complete",
                json={"moveIncompleteTo": "backlog"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "User does not have permission" in data["error"]

    def test_non_json_error_response(self, client):
        with patch(PATCH_BASE_URL, "https://test.atlassian.net"), \
             patch("proxy.httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_cls.return_value.__aenter__.return_value = mock_http
            mock_http.get.return_value = _mock_response(200, {"issues": []})
            bad_r = MagicMock()
            bad_r.status_code = 500
            bad_r.json.side_effect = ValueError("not JSON")
            mock_http.post.return_value = bad_r

            resp = client.post(
                "/proxy/jira/sprint/171/complete",
                json={"moveIncompleteTo": "backlog"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "500" in data["error"]

    def test_jira_not_configured(self, client):
        with patch(PATCH_BASE_URL, ""):
            resp = client.post(
                "/proxy/jira/sprint/171/complete",
                json={"moveIncompleteTo": "backlog"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "error" in data
