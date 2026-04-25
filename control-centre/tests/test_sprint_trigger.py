"""Tests for sprint trigger API."""
import pytest
from unittest.mock import Mock, patch
from control-centre.api.sprint_trigger import SprintTriggerAPI


class TestSprintTriggerAPI:
    """Test cases for SprintTriggerAPI."""

    @patch.dict('os.environ', {'CI_API_TOKEN': 'test-token', 'CI_API_URL': 'https://test.api'})
    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        api = SprintTriggerAPI()
        assert api.api_token == 'test-token'
        assert api.base_url == 'https://test.api'

    @patch.dict('os.environ', {}, clear=True)
    def test_init_without_token_raises_error(self):
        """Test initialization without API token raises ValueError."""
        with pytest.raises(ValueError, match='CI_API_TOKEN'):
            SprintTriggerAPI()

    @patch.dict('os.environ', {'CI_API_TOKEN': 'test-token'})
    @patch('requests.post')
    def test_trigger_sprint_success(self, mock_post):
        """Test successful sprint trigger."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': '12345',
            'web_url': 'https://ci.example.com/pipeline/12345',
            'status': 'pending',
            'created_at': '2024-01-01T00:00:00Z',
        }
        mock_post.return_value = mock_response

        api = SprintTriggerAPI()
        result = api.trigger_sprint('project-123')

        assert result['pipeline_id'] == '12345'
        assert result['status'] == 'pending'
        mock_post.assert_called_once()

    @patch.dict('os.environ', {'CI_API_TOKEN': 'test-token'})
    @patch('requests.get')
    def test_get_pipeline_status(self, mock_get):
        """Test getting pipeline status."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': '12345',
            'status': 'success',
            'web_url': 'https://ci.example.com/pipeline/12345',
            'duration': 120,
            'finished_at': '2024-01-01T00:05:00Z',
        }
        mock_get.return_value = mock_response

        api = SprintTriggerAPI()
        result = api.get_pipeline_status('project-123', '12345')

        assert result['status'] == 'success'
        assert result['duration'] == 120
