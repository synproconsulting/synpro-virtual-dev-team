"""Tests for SonarCloud client."""

import os
from unittest.mock import Mock, patch

import httpx
import pytest

from src.auth.sonarcloud_client import SonarCloudClient


class TestSonarCloudClient:
    """Test cases for SonarCloudClient."""

    def test_init_with_token(self) -> None:
        """Test client initialization with explicit token."""
        client = SonarCloudClient(token="test-token")
        assert client.token == "test-token"
        assert client.base_url == "https://sonarcloud.io/api"
        client.close()

    def test_init_with_env_token(self) -> None:
        """Test client initialization with environment variable."""
        with patch.dict(os.environ, {"SONARCLOUD_TOKEN": "env-token"}):
            client = SonarCloudClient()
            assert client.token == "env-token"
            client.close()

    def test_init_without_token_raises_error(self) -> None:
        """Test client initialization without token raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="SonarCloud token must be provided"):
                SonarCloudClient()

    def test_context_manager(self) -> None:
        """Test client works as context manager."""
        with SonarCloudClient(token="test-token") as client:
            assert client.token == "test-token"

    @patch("httpx.Client.post")
    def test_trigger_analysis_success(self, mock_post: Mock) -> None:
        """Test successful analysis trigger."""
        mock_response = Mock()
        mock_response.json.return_value = {"taskId": "AX123", "status": "PENDING"}
        mock_post.return_value = mock_response

        with SonarCloudClient(token="test-token") as client:
            result = client.trigger_analysis("my-project", branch="main")

        assert result["taskId"] == "AX123"
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    @patch("httpx.Client.get")
    def test_get_analysis_status_success(self, mock_get: Mock) -> None:
        """Test successful retrieval of analysis status."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "projectStatus": {"status": "OK", "conditions": []}
        }
        mock_get.return_value = mock_response

        with SonarCloudClient(token="test-token") as client:
            result = client.get_analysis_status("my-project")

        assert result["projectStatus"]["status"] == "OK"
        mock_get.assert_called_once()

    @patch("httpx.Client.get")
    def test_get_measures_success(self, mock_get: Mock) -> None:
        """Test successful retrieval of measures."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "component": {"measures": [{"metric": "coverage", "value": "85.5"}]}
        }
        mock_get.return_value = mock_response

        with SonarCloudClient(token="test-token") as client:
            result = client.get_measures("my-project", ["coverage", "bugs"])

        assert len(result["component"]["measures"]) == 1
        mock_get.assert_called_once()

    @patch("httpx.Client.post")
    def test_trigger_analysis_http_error(self, mock_post: Mock) -> None:
        """Test analysis trigger handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=Mock(), response=Mock()
        )
        mock_post.return_value = mock_response

        with SonarCloudClient(token="test-token") as client:
            with pytest.raises(httpx.HTTPStatusError):
                client.trigger_analysis("my-project")
