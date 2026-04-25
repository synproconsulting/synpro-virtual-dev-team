"""Tests for reviews API handlers."""

import pytest
from unittest.mock import patch, Mock
from control-centre.api.reviews import (
    fetch_pr_reviews,
    trigger_pr_review,
    get_review_details,
    ReviewAPIError
)


class TestReviewsAPI:
    """Test cases for reviews API functions."""

    @patch('control-centre.api.reviews.requests.get')
    @patch('control-centre.api.reviews.get_auth_token')
    @patch('control-centre.api.reviews.get_api_base_url')
    def test_fetch_pr_reviews_success(self, mock_base_url, mock_token, mock_get):
        """Test successful PR reviews fetch."""
        mock_base_url.return_value = 'http://test.com'
        mock_token.return_value = 'test-token'
        mock_response = Mock()
        mock_response.json.return_value = {
            'reviews': [
                {'pr_number': 1, 'status': 'approved'},
                {'pr_number': 2, 'status': 'pending'}
            ]
        }
        mock_get.return_value = mock_response

        result = fetch_pr_reviews()
        
        assert len(result) == 2
        assert result[0]['pr_number'] == 1
        assert result[1]['status'] == 'pending'

    @patch('control-centre.api.reviews.requests.get')
    @patch('control-centre.api.reviews.get_auth_token')
    @patch('control-centre.api.reviews.get_api_base_url')
    def test_fetch_pr_reviews_empty(self, mock_base_url, mock_token, mock_get):
        """Test PR reviews fetch with empty result."""
        mock_base_url.return_value = 'http://test.com'
        mock_token.return_value = 'test-token'
        mock_response = Mock()
        mock_response.json.return_value = {'reviews': []}
        mock_get.return_value = mock_response

        result = fetch_pr_reviews()
        
        assert len(result) == 0

    @patch('control-centre.api.reviews.requests.post')
    @patch('control-centre.api.reviews.get_auth_token')
    @patch('control-centre.api.reviews.get_api_base_url')
    def test_trigger_pr_review_success(self, mock_base_url, mock_token, mock_post):
        """Test successful PR review trigger."""
        mock_base_url.return_value = 'http://test.com'
        mock_token.return_value = 'test-token'
        mock_response = Mock()
        mock_response.json.return_value = {'review_id': 'abc123', 'status': 'triggered'}
        mock_post.return_value = mock_response

        result = trigger_pr_review(42)
        
        assert result['review_id'] == 'abc123'
        assert result['status'] == 'triggered'

    @patch('control-centre.api.reviews.requests.get')
    @patch('control-centre.api.reviews.get_auth_token')
    @patch('control-centre.api.reviews.get_api_base_url')
    def test_get_review_details_success(self, mock_base_url, mock_token, mock_get):
        """Test successful review details retrieval."""
        mock_base_url.return_value = 'http://test.com'
        mock_token.return_value = 'test-token'
        mock_response = Mock()
        mock_response.json.return_value = {
            'pr_number': 42,
            'status': 'approved',
            'comments': ['LGTM']
        }
        mock_get.return_value = mock_response

        result = get_review_details(42)
        
        assert result['pr_number'] == 42
        assert result['status'] == 'approved'
        assert len(result['comments']) == 1
