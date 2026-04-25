"""Tests for sprint API handlers."""

import pytest
from unittest.mock import patch, Mock
from control-centre.api.sprint import (
    trigger_sprint,
    get_sprint_status,
    SprintAPIError,
    get_api_base_url,
    get_auth_token
)


class TestSprintAPI:
    """Test cases for sprint API functions."""

    @patch('control-centre.api.sprint.os.getenv')
    def test_get_api_base_url_with_env(self, mock_getenv):
        """Test API base URL retrieval from environment."""
        mock_getenv.return_value = 'https://api.example.com'
        assert get_api_base_url() == 'https://api.example.com'

    @patch('control-centre.api.sprint.os.getenv')
    def test_get_api_base_url_default(self, mock_getenv):
        """Test API base URL default value."""
        mock_getenv.return_value = None
        assert get_api_base_url() == 'http://localhost:8000'

    @patch('control-centre.api.sprint.os.getenv')
    def test_get_auth_token_missing(self, mock_getenv):
        """Test auth token retrieval when missing."""
        mock_getenv.return_value = None
        with pytest.raises(SprintAPIError, match='SPRINT_API_TOKEN'):
            get_auth_token()

    @patch('control-centre.api.sprint.requests.post')
    @patch('control-centre.api.sprint.get_auth_token')
    @patch('control-centre.api.sprint.get_api_base_url')
    def test_trigger_sprint_success(self, mock_base_url, mock_token, mock_post):
        """Test successful sprint trigger."""
        mock_base_url.return_value = 'http://test.com'
        mock_token.return_value = 'test-token'
        mock_response = Mock()
        mock_response.json.return_value = {'run_id': '12345', 'status': 'started'}
        mock_post.return_value = mock_response

        result = trigger_sprint()
        
        assert result['run_id'] == '12345'
        assert result['status'] == 'started'
        mock_post.assert_called_once()

    @patch('control-centre.api.sprint.requests.post')
    @patch('control-centre.api.sprint.get_auth_token')
    @patch('control-centre.api.sprint.get_api_base_url')
    def test_trigger_sprint_failure(self, mock_base_url, mock_token, mock_post):
        """Test sprint trigger failure."""
        mock_base_url.return_value = 'http://test.com'
        mock_token.return_value = 'test-token'
        mock_post.side_effect = Exception('Network error')

        with pytest.raises(SprintAPIError, match='Failed to trigger sprint'):
            trigger_sprint()

    @patch('control-centre.api.sprint.requests.get')
    @patch('control-centre.api.sprint.get_auth_token')
    @patch('control-centre.api.sprint.get_api_base_url')
    def test_get_sprint_status_success(self, mock_base_url, mock_token, mock_get):
        """Test successful sprint status retrieval."""
        mock_base_url.return_value = 'http://test.com'
        mock_token.return_value = 'test-token'
        mock_response = Mock()
        mock_response.json.return_value = {'run_id': '12345', 'status': 'completed'}
        mock_get.return_value = mock_response

        result = get_sprint_status('12345')
        
        assert result['run_id'] == '12345'
        assert result['status'] == 'completed'
