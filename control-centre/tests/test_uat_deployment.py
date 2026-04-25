"""Tests for UAT deployment functionality."""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.uat_deployment import (
    UATDeploymentService,
    get_services_handler,
    deploy_handler
)


class TestUATDeploymentService(unittest.TestCase):
    """Test cases for UATDeploymentService."""

    def setUp(self):
        self.service = UATDeploymentService()

    def test_get_default_services(self):
        """Test getting default services."""
        services = self.service._get_default_services()
        self.assertIsInstance(services, list)
        self.assertGreater(len(services), 0)
        self.assertIn('name', services[0])
        self.assertIn('current_version', services[0])

    @patch('os.path.exists')
    def test_get_available_services_no_config(self, mock_exists):
        """Test getting services when config doesn't exist."""
        mock_exists.return_value = False
        services = self.service.get_available_services()
        self.assertIsInstance(services, list)
        self.assertGreater(len(services), 0)

    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps({
        'services': [
            {'name': 'test-service', 'current_version': 'v1.0.0', 'status': 'running'}
        ]
    }))
    @patch('os.path.exists')
    def test_get_available_services_with_config(self, mock_exists, mock_file):
        """Test getting services from config file."""
        mock_exists.return_value = True
        services = self.service.get_available_services()
        self.assertEqual(len(services), 1)
        self.assertEqual(services[0]['name'], 'test-service')

    def test_validate_deployment_request_empty_services(self):
        """Test validation with empty services list."""
        is_valid, error = self.service.validate_deployment_request([], 'main')
        self.assertFalse(is_valid)
        self.assertIn('No services', error)

    def test_validate_deployment_request_empty_branch(self):
        """Test validation with empty branch."""
        is_valid, error = self.service.validate_deployment_request(['service1'], '')
        self.assertFalse(is_valid)
        self.assertIn('Branch name', error)

    @patch.object(UATDeploymentService, 'get_available_services')
    def test_validate_deployment_request_invalid_service(self, mock_services):
        """Test validation with invalid service name."""
        mock_services.return_value = [
            {'name': 'valid-service', 'current_version': 'v1.0.0'}
        ]
        is_valid, error = self.service.validate_deployment_request(
            ['invalid-service'], 'main'
        )
        self.assertFalse(is_valid)
        self.assertIn('Invalid services', error)

    @patch.object(UATDeploymentService, 'get_available_services')
    def test_validate_deployment_request_valid(self, mock_services):
        """Test validation with valid request."""
        mock_services.return_value = [
            {'name': 'api-gateway', 'current_version': 'v1.0.0'}
        ]
        is_valid, error = self.service.validate_deployment_request(
            ['api-gateway'], 'main'
        )
        self.assertTrue(is_valid)
        self.assertEqual(error, '')

    def test_trigger_deployment(self):
        """Test triggering a deployment."""
        result = self.service.trigger_deployment(
            ['api-gateway', 'user-service'],
            'develop',
            'uat'
        )
        self.assertIn('deployment_id', result)
        self.assertEqual(result['status'], 'initiated')
        self.assertEqual(result['branch'], 'develop')
        self.assertEqual(len(result['services']), 2)


class TestUATDeploymentHandlers(unittest.TestCase):
    """Test cases for API handlers."""

    @patch('api.uat_deployment.UATDeploymentService')
    def test_get_services_handler_success(self, mock_service_class):
        """Test successful services retrieval."""
        mock_service = MagicMock()
        mock_service.get_available_services.return_value = [
            {'name': 'test-service', 'current_version': 'v1.0.0'}
        ]
        mock_service_class.return_value = mock_service

        response, status_code = get_services_handler(None)
        self.assertEqual(status_code, 200)
        self.assertIn('services', response)
        self.assertEqual(len(response['services']), 1)

    @patch('api.uat_deployment.UATDeploymentService')
    def test_deploy_handler_success(self, mock_service_class):
        """Test successful deployment trigger."""
        mock_service = MagicMock()
        mock_service.validate_deployment_request.return_value = (True, '')
        mock_service.trigger_deployment.return_value = {
            'deployment_id': 'test-123',
            'status': 'initiated'
        }
        mock_service_class.return_value = mock_service

        mock_request = MagicMock()
        mock_request.get_json.return_value = {
            'services': ['api-gateway'],
            'branch': 'main',
            'environment': 'uat'
        }

        response, status_code = deploy_handler(mock_request)
        self.assertEqual(status_code, 200)
        self.assertIn('deployment_id', response)

    @patch('api.uat_deployment.UATDeploymentService')
    def test_deploy_handler_validation_error(self, mock_service_class):
        """Test deployment with validation error."""
        mock_service = MagicMock()
        mock_service.validate_deployment_request.return_value = (
            False, 'Invalid services'
        )
        mock_service_class.return_value = mock_service

        mock_request = MagicMock()
        mock_request.get_json.return_value = {
            'services': ['invalid'],
            'branch': 'main'
        }

        response, status_code = deploy_handler(mock_request)
        self.assertEqual(status_code, 400)
        self.assertIn('error', response)


if __name__ == '__main__':
    unittest.main()
