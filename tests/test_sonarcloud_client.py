"""Tests for SonarCloud client."""

import os
from unittest.mock import Mock, patch

import httpx
import pytest

from src.auth.sonarcloud_client import SonarCloudClient


class TestSonarCloudClient:
    """Test cases for SonarCloudClient."""

    def test_init_with_token(self) -> None:
        """Test initialization with explicit token."""
        client = SonarCloudClient(token="test-token")
        assert client.token == "test-token"
        assert client.base_url == "https://sonarcloud.io/api"
        client.close()

    def test_init_with_env_var(self) -> None:
        """Test initialization with environment variable."""
        with patch.dict(os.environ, {"SONARCLOUD_TOKEN": "env-token"}):
            client = SonarCloudClient()
            assert client.token == "env-token"
            client.close()

    def test_init_without_token_raises(self) -> None:
        """Test initialization without token raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="SonarCloud token must be provided"):
                SonarCloudClient()

    def test_trigger_analysis(self) -> None:
        """Test triggering analysis."""
        mock_response = Mock()
        mock_response.json.return_value = {"taskId": "task-123"}
        mock_response.raise_for_status = Mock()

        with patch("httpx.Client.post", return_value=mock_response) as mock_post:
            client = SonarCloudClient(token="test-token")
            result = client.trigger_analysis("my-project", "main")

            assert result == {"taskId": "task-123"}
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "projectKey=my-project" in str(call_args)
            assert "branch=main" in str(call_args)
            client.close()

    def test_get_project_status(self) -> None:
        """Test getting project status."""
        mock_response = Mock()
        mock_response.json.return_value = {"projectStatus": {"status": "OK"}}
        mock_response.raise_for_status = Mock()

        with patch("httpx.Client.get", return_value=mock_response) as mock_get:
            client = SonarCloudClient(token="test-token")
            result = client.get_project_status("my-project")

            assert result["projectStatus"]["status"] == "OK"
            mock_get.assert_called_once()
            client.close()

    def test_get_measures(self) -> None:
        """Test getting measures."""
        mock_response = Mock()
        mock_response.json.return_value = {"component": {"measures": [{"metric": "bugs", "value": "0"}]}}
        mock_response.raise_for_status = Mock()

        with patch("httpx.Client.get", return_value=mock_response) as mock_get:
            client = SonarCloudClient(token="test-token")
            result = client.get_measures("my-project", ["bugs", "coverage"])

            assert "component" in result
            call_args = mock_get.call_args
            assert "metricKeys=bugs%2Ccoverage" in str(call_args) or "metricKeys=bugs,coverage" in str(call_args)
            client.close()

    def test_get_issues(self) -> None:
        """Test getting issues."""
        mock_response = Mock()
        mock_response.json.return_value = {"issues": [], "total": 0}
        mock_response.raise_for_status = Mock()

        with patch("httpx.Client.get", return_value=mock_response) as mock_get:
            client = SonarCloudClient(token="test-token")
            result = client.get_issues("my-project", branch="main", page=2)

            assert result["total"] == 0
            call_args = mock_get.call_args
            assert "p=2" in str(call_args)
            client.close()

    def test_context_manager(self) -> None:
        """Test using client as context manager."""
        with SonarCloudClient(token="test-token") as client:
            assert client.token == "test-token"
