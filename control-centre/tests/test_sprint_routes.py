"""Tests for sprint API routes."""
import pytest
from unittest.mock import patch
from flask import Flask
from control_centre.api.sprint_routes import sprint_bp


@pytest.fixture
def app():
    """Create Flask app for testing."""
    app = Flask(__name__)
    app.register_blueprint(sprint_bp)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestSprintRoutes:
    """Test cases for sprint API routes."""

    @patch('control_centre.api.sprint_routes.fetch_sprint_status')
    def test_get_sprint_status_success(self, mock_fetch, client):
        """Test successful sprint status retrieval."""
        mock_fetch.return_value = {
            'name': 'Sprint 45',
            'metrics': {'totalIssues': 10},
            'jiraIssues': [],
            'pullRequests': [],
            'ciBuilds': [],
        }

        response = client.get('/api/sprint/123/status')
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'Sprint 45'
        assert 'metrics' in data

    @patch('control_centre.api.sprint_routes.fetch_sprint_status')
    def test_get_sprint_status_error(self, mock_fetch, client):
        """Test error handling in sprint status endpoint."""
        mock_fetch.side_effect = Exception('Test error')

        response = client.get('/api/sprint/123/status')
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data

    def test_get_active_sprints(self, client):
        """Test active sprints endpoint."""
        response = client.get('/api/sprint/active')
        assert response.status_code == 200
        data = response.get_json()
        assert 'sprints' in data
