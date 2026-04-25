"""Tests for auto review API."""
import pytest
from unittest.mock import Mock, patch
from control-centre.api.auto_review import AutoReviewAPI


class TestAutoReviewAPI:
    """Test cases for AutoReviewAPI."""

    @patch.dict('os.environ', {
        'VCS_API_TOKEN': 'test-token',
        'VCS_API_URL': 'https://vcs.test',
        'REVIEW_SERVICE_URL': 'https://review.test'
    })
    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        api = AutoReviewAPI()
        assert api.api_token == 'test-token'
        assert api.base_url == 'https://vcs.test'
        assert api.review_service_url == 'https://review.test'

    @patch.dict('os.environ', {}, clear=True)
    def test_init_without_token_raises_error(self):
        """Test initialization without API token raises ValueError."""
        with pytest.raises(ValueError, match='VCS_API_TOKEN'):
            AutoReviewAPI()

    @patch.dict('os.environ', {'VCS_API_TOKEN': 'test-token'})
    @patch('requests.get')
    def test_get_open_pull_requests(self, mock_get):
        """Test fetching open pull requests."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'iid': 1,
                'title': 'Test PR',
                'author': {'username': 'testuser'},
                'source_branch': 'feature',
                'target_branch': 'main',
                'web_url': 'https://git.example.com/pr/1',
                'created_at': '2024-01-01T00:00:00Z',
            }
        ]
        mock_get.return_value = mock_response

        api = AutoReviewAPI()
        result = api.get_open_pull_requests('project-123')

        assert len(result) == 1
        assert result[0]['title'] == 'Test PR'
        assert result[0]['author'] == 'testuser'

    @patch.dict('os.environ', {'VCS_API_TOKEN': 'test-token'})
    @patch('requests.post')
    @patch('requests.get')
    def test_trigger_auto_review(self, mock_get, mock_post):
        """Test triggering auto review."""
        # Mock PR details
        pr_mock = Mock()
        pr_mock.json.return_value = {
            'title': 'Test PR',
            'source_branch': 'feature',
            'target_branch': 'main',
            'diff_refs': {'base_sha': 'abc123'},
        }
        
        # Mock review trigger
        review_mock = Mock()
        review_mock.json.return_value = {
            'review_id': 'rev-123',
            'status': 'in_progress',
            'estimated_completion': '5m',
        }
        
        mock_get.return_value = pr_mock
        mock_post.return_value = review_mock

        api = AutoReviewAPI()
        result = api.trigger_auto_review('project-123', '1')

        assert result['review_id'] == 'rev-123'
        assert result['status'] == 'in_progress'
