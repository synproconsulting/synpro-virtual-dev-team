"""
Tests for Railway deployment validator.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from railway_deploy_validator import (
    RailwayDeployValidator,
    ValidationResult,
    DeploymentStatus
)


@pytest.fixture
def mock_railway_token():
    """Mock Railway API token."""
    return "test_railway_token_12345"


@pytest.fixture
def mock_project_id():
    """Mock Railway project ID."""
    return "test_project_id_67890"


@pytest.fixture
def validator(mock_railway_token, mock_project_id):
    """Create a validator instance with mocked credentials."""
    return RailwayDeployValidator(mock_railway_token, mock_project_id)


@pytest.fixture
def mock_project_response():
    """Mock Railway API project response."""
    return {
        "data": {
            "project": {
                "id": "test_project_id",
                "name": "Test Project",
                "environments": {
                    "edges": [
                        {
                            "node": {
                                "id": "env_prod_123",
                                "name": "production"
                            }
                        },
                        {
                            "node": {
                                "id": "env_staging_456",
                                "name": "staging"
                            }
                        }
                    ]
                },
                "services": {
                    "edges": [
                        {
                            "node": {
                                "id": "svc_backend_789",
                                "name": "synpro-virtual-dev-team"
                            }
                        },
                        {
                            "node": {
                                "id": "svc_frontend_012",
                                "name": "Virtual-Dev-Team-UAT-Frontend"
                            }
                        }
                    ]
                }
            }
        }
    }


class TestRailwayDeployValidator:
    """Test suite for RailwayDeployValidator."""
    
    def test_initialization(self, validator, mock_railway_token, mock_project_id):
        """Test validator initialization."""
        assert validator.railway_token == mock_railway_token
        assert validator.project_id == mock_project_id
        assert validator.GRAPHQL_ENDPOINT == "https://backboard.railway.app/graphql/v2"
        assert "Authorization" in validator.session.headers
        assert validator.session.headers["Authorization"] == f"Bearer {mock_railway_token}"
    
    @patch('railway_deploy_validator.requests.Session.post')
    def test_execute_graphql_query_success(self, mock_post, validator):
        """Test successful GraphQL query execution."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"test": "value"}
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = validator._execute_graphql_query("{ test }")
        
        assert result == {"data": {"test": "value"}}
        mock_post.assert_called_once()
    
    @patch('railway_deploy_validator.requests.Session.post')
    def test_execute_graphql_query_with_errors(self, mock_post, validator):
        """Test GraphQL query with errors in response."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "errors": [{"message": "Test error"}]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        with pytest.raises(ValueError, match="GraphQL errors"):
            validator._execute_graphql_query("{ test }")
    
    @patch.object(RailwayDeployValidator, '_execute_graphql_query')
    def test_get_project_info(self, mock_query, validator, mock_project_response):
        """Test retrieving project information."""
        mock_query.return_value = mock_project_response
        
        result = validator.get_project_info()
        
        assert result["id"] == "test_project_id"
        assert result["name"] == "Test Project"
        assert len(result["environments"]["edges"]) == 2
        assert len(result["services"]["edges"]) == 2
    
    @patch.object(RailwayDeployValidator, '_execute_graphql_query')
    def test_get_service_deployments(self, mock_query, validator):
        """Test retrieving service deployments."""
        mock_query.return_value = {
            "data": {
                "deployments": {
                    "edges": [
                        {
                            "node": {
                                "id": "deploy_123",
                                "status": "SUCCESS",
                                "createdAt": "2024-01-01T00:00:00Z"
                            }
                        }
                    ]
                }
            }
        }
        
        deployments = validator.get_service_deployments("svc_123", "env_456", limit=5)
        
        assert len(deployments) == 1
        assert deployments[0]["id"] == "deploy_123"
        assert deployments[0]["status"] == "SUCCESS"
    
    @patch.object(RailwayDeployValidator, 'get_project_info')
    def test_resolve_service_and_environment_success(
        self,
        mock_get_project,
        validator,
        mock_project_response
    ):
        """Test successful service and environment resolution."""
        mock_get_project.return_value = mock_project_response["data"]["project"]
        
        svc_id, env_id = validator.resolve_service_and_environment(
            "synpro-virtual-dev-team",
            "production"
        )
        
        assert svc_id == "svc_backend_789"
        assert env_id == "env_prod_123"
    
    @patch.object(RailwayDeployValidator, 'get_project_info')
    def test_resolve_service_and_environment_not_found(
        self,
        mock_get_project,
        validator,
        mock_project_response
    ):
        """Test service/environment resolution when not found."""
        mock_get_project.return_value = mock_project_response["data"]["project"]
        
        svc_id, env_id = validator.resolve_service_and_environment(
            "nonexistent-service",
            "production"
        )
        
        assert svc_id is None
        assert env_id == "env_prod_123"
    
    @patch.object(RailwayDeployValidator, '_execute_graphql_query')
    def test_trigger_redeploy_success(self, mock_query, validator):
        """Test successful redeploy trigger."""
        mock_query.return_value = {
            "data": {
                "serviceInstanceRedeploy": "deploy_new_123"
            }
        }
        
        result = validator.trigger_redeploy("svc_123", "env_456")
        
        assert result.success is True
        assert "triggered successfully" in result.message
        assert result.deployment_id == "deploy_new_123"
    
    @patch.object(RailwayDeployValidator, '_execute_graphql_query')
    def test_trigger_redeploy_failure(self, mock_query, validator):
        """Test failed redeploy trigger."""
        mock_query.side_effect = ValueError("API error")
        
        result = validator.trigger_redeploy("svc_123", "env_456")
        
        assert result.success is False
        assert "Failed to trigger redeploy" in result.message
    
    @patch.object(RailwayDeployValidator, 'get_service_deployments')
    def test_validate_deployment_status_success(self, mock_get_deployments, validator):
        """Test deployment status validation - success case."""
        mock_get_deployments.return_value = [
            {
                "id": "deploy_123",
                "status": "SUCCESS",
                "meta": {}
            }
        ]
        
        result = validator.validate_deployment_status(
            "svc_123",
            "env_456",
            timeout_seconds=30,
            check_interval=1
        )
        
        assert result.success is True
        assert result.deployment_id == "deploy_123"
        assert result.status == "SUCCESS"
    
    @patch.object(RailwayDeployValidator, 'get_service_deployments')
    def test_validate_deployment_status_failed(self, mock_get_deployments, validator):
        """Test deployment status validation - failed case."""
        mock_get_deployments.return_value = [
            {
                "id": "deploy_123",
                "status": "FAILED",
                "meta": {"error": "Build failed"}
            }
        ]
        
        result = validator.validate_deployment_status(
            "svc_123",
            "env_456",
            timeout_seconds=30,
            check_interval=1
        )
        
        assert result.success is False
        assert result.deployment_id == "deploy_123"
        assert result.status == "FAILED"
        assert "failed with status: FAILED" in result.message
    
    @patch.object(RailwayDeployValidator, 'get_service_deployments')
    def test_validate_deployment_status_no_deployments(
        self,
        mock_get_deployments,
        validator
    ):
        """Test deployment status validation when no deployments found."""
        mock_get_deployments.return_value = []
        
        result = validator.validate_deployment_status(
            "svc_123",
            "env_456",
            timeout_seconds=30,
            check_interval=1
        )
        
        assert result.success is False
        assert "No deployments found" in result.message
    
    @patch.object(RailwayDeployValidator, 'get_project_info')
    def test_validate_api_connectivity_success(
        self,
        mock_get_project,
        validator,
        mock_project_response
    ):
        """Test successful API connectivity validation."""
        mock_get_project.return_value = mock_project_response["data"]["project"]
        
        result = validator.validate_api_connectivity()
        
        assert result.success is True
        assert "connectivity validated" in result.message
        assert "Test Project" in result.message
    
    @patch.object(RailwayDeployValidator, 'get_project_info')
    def test_validate_api_connectivity_failure(self, mock_get_project, validator):
        """Test API connectivity validation failure."""
        mock_get_project.side_effect = ConnectionError("Network error")
        
        result = validator.validate_api_connectivity()
        
        assert result.success is False
        assert "connectivity check failed" in result.message or "Unexpected error" in result.message


class TestValidationResult:
    """Test suite for ValidationResult dataclass."""
    
    def test_validation_result_success(self):
        """Test successful validation result."""
        result = ValidationResult(
            success=True,
            message="Test success",
            deployment_id="deploy_123"
        )
        
        assert result.success is True
        assert result.message == "Test success"
        assert result.deployment_id == "deploy_123"
        assert result.status is None
        assert result.error_details is None
    
    def test_validation_result_failure(self):
        """Test failed validation result with error details."""
        error_details = {"error": "Build failed", "code": 500}
        result = ValidationResult(
            success=False,
            message="Test failure",
            error_details=error_details
        )
        
        assert result.success is False
        assert result.message == "Test failure"
        assert result.error_details == error_details


class TestDeploymentStatus:
    """Test suite for DeploymentStatus enum."""
    
    def test_deployment_status_values(self):
        """Test DeploymentStatus enum values."""
        assert DeploymentStatus.SUCCESS.value == "SUCCESS"
        assert DeploymentStatus.FAILED.value == "FAILED"
        assert DeploymentStatus.BUILDING.value == "BUILDING"
        assert DeploymentStatus.DEPLOYING.value == "DEPLOYING"
        assert DeploymentStatus.CRASHED.value == "CRASHED"
        assert DeploymentStatus.REMOVED.value == "REMOVED"
        assert DeploymentStatus.UNKNOWN.value == "UNKNOWN"
