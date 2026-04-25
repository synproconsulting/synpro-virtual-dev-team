import pytest
import json
from unittest.mock import Mock, patch
from flask import Flask
from control-centre.api.pm_agent_routes import register_routes


@pytest.fixture
def app():
    """Create test Flask app."""
    app = Flask(__name__)
    register_routes(app)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestPMAgentRoutes:
    """Test suite for PM Agent routes."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get('/api/pm-agent/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data

    def test_chat_without_auth(self, client):
        """Test chat endpoint requires authentication."""
        response = client.post('/api/pm-agent/chat', json={})
        assert response.status_code == 401

    @patch('control-centre.api.pm_agent_routes.pm_handler')
    def test_chat_missing_params(self, mock_handler, client):
        """Test chat endpoint validates parameters."""
        mock_handler.return_value = Mock()
        
        response = client.post(
            '/api/pm-agent/chat',
            json={},
            headers={'Authorization': 'Bearer test-token'}
        )
        assert response.status_code == 400

    @patch('control-centre.api.pm_agent_routes.pm_handler')
    def test_chat_success(self, mock_handler, client):
        """Test successful chat interaction."""
        mock_handler.process_chat_message.return_value = {
            'message': 'Test response',
            'sprint_plan': None,
            'requires_approval': False
        }
        
        response = client.post(
            '/api/pm-agent/chat',
            json={
                'project_id': 'proj-1',
                'message': 'Hello',
                'conversation_history': []
            },
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Test response'

    def test_approve_sprint_without_auth(self, client):
        """Test approve endpoint requires authentication."""
        response = client.post('/api/pm-agent/approve-sprint', json={})
        assert response.status_code == 401

    @patch('control-centre.api.pm_agent_routes.pm_handler')
    def test_approve_sprint_missing_params(self, mock_handler, client):
        """Test approve endpoint validates parameters."""
        mock_handler.return_value = Mock()
        
        response = client.post(
            '/api/pm-agent/approve-sprint',
            json={},
            headers={'Authorization': 'Bearer test-token'}
        )
        assert response.status_code == 400

    @patch('control-centre.api.pm_agent_routes.pm_handler')
    def test_approve_sprint_success(self, mock_handler, client):
        """Test successful sprint approval."""
        mock_handler.create_sprint_from_plan.return_value = {
            'id': 'sprint-1',
            'name': 'Sprint 1',
            'status': 'planned'
        }
        
        response = client.post(
            '/api/pm-agent/approve-sprint',
            json={
                'project_id': 'proj-1',
                'sprint_plan': {'name': 'Sprint 1', 'duration': 14, 'stories': [], 'total_points': 0},
                'approved': True
            },
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'sprint' in data

    @patch('control-centre.api.pm_agent_routes.pm_handler')
    def test_reject_sprint(self, mock_handler, client):
        """Test sprint rejection."""
        response = client.post(
            '/api/pm-agent/approve-sprint',
            json={
                'project_id': 'proj-1',
                'sprint_plan': {'name': 'Sprint 1'},
                'approved': False
            },
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True