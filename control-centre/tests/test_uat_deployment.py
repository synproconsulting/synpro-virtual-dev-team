"""Tests for UAT deployment functionality."""
import pytest
import json
from unittest.mock import Mock, patch
from control-centre.api.uat_deployment import (
    UATDeploymentService,
    uat_bp
)


class TestUATDeploymentService:
    """Test cases for UATDeploymentService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = UATDeploymentService()
    
    def test_get_available_services(self):
        """Test retrieving available services."""
        services = self.service.get_available_services()
        
        assert isinstance(services, list)
        assert len(services) > 0
        
        for service in services:
            assert 'id' in service
            assert 'name' in service
            assert 'version' in service
            assert 'status' in service
    
    def test_deploy_services_success(self):
        """Test successful service deployment."""
        service_ids = ['api-gateway', 'user-service']
        user = 'test@example.com'
        
        result = self.service.deploy_services(service_ids, user)
        
        assert result['status'] == 'success'
        assert 'deployment_id' in result
        assert len(result['services']) == 2
        assert 'API Gateway' in result['services']
        assert 'User Service' in result['services']
    
    def test_deploy_services_empty_list(self):
        """Test deployment with empty service list."""
        with pytest.raises(ValueError):
            self.service.deploy_services([], 'test@example.com')
    
    def test_deploy_services_invalid_ids(self):
        """Test deployment with invalid service IDs."""
        with pytest.raises(ValueError):
            self.service.deploy_services(['invalid-service'], 'test@example.com')
    
    def test_get_deployment_history(self):
        """Test retrieving deployment history."""
        history = self.service.get_deployment_history()
        
        assert isinstance(history, list)
        
        if len(history) > 0:
            deployment = history[0]
            assert 'id' in deployment
            assert 'services' in deployment
            assert 'status' in deployment
            assert 'timestamp' in deployment
            assert 'user' in deployment
    
    def test_get_deployment_history_with_limit(self):
        """Test retrieving deployment history with limit."""
        history = self.service.get_deployment_history(limit=10)
        
        assert isinstance(history, list)
        assert len(history) <= 10


class TestUATDeploymentAPI:
    """Test cases for UAT deployment API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from flask import Flask
        app = Flask(__name__)
        app.register_blueprint(uat_bp)
        app.config['TESTING'] = True
        return app.test_client()
    
    def test_get_services_endpoint(self, client):
        """Test GET /api/uat/services endpoint."""
        response = client.get('/api/uat/services')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'services' in data
        assert isinstance(data['services'], list)
    
    def test_deploy_endpoint_success(self, client):
        """Test POST /api/uat/deploy endpoint with valid data."""
        payload = {
            'service_ids': ['api-gateway', 'user-service']
        }
        
        response = client.post(
            '/api/uat/deploy',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'X-User-Email': 'test@example.com'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'deployment_id' in data
    
    def test_deploy_endpoint_no_services(self, client):
        """Test POST /api/uat/deploy endpoint with no services."""
        payload = {'service_ids': []}
        
        response = client.post(
            '/api/uat/deploy',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_deployment_history_endpoint(self, client):
        """Test GET /api/uat/deployments/history endpoint."""
        response = client.get('/api/uat/deployments/history')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'deployments' in data
        assert isinstance(data['deployments'], list)