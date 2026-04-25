"""UAT Deployment API handlers."""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
import uuid

logger = logging.getLogger(__name__)


class UATDeploymentService:
    """Service for managing UAT deployments."""

    def __init__(self):
        self.deployment_config_path = os.getenv(
            'UAT_DEPLOYMENT_CONFIG',
            '/etc/control-centre/uat-services.json'
        )
        self.deployment_endpoint = os.getenv(
            'UAT_DEPLOYMENT_API',
            'http://deployment-service:8080/api/v1/deploy'
        )

    def get_available_services(self) -> List[Dict[str, Any]]:
        """Fetch available services for UAT deployment."""
        try:
            if os.path.exists(self.deployment_config_path):
                with open(self.deployment_config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('services', [])
            else:
                # Return default services if config not found
                return self._get_default_services()
        except Exception as e:
            logger.error(f"Failed to load services: {e}")
            return self._get_default_services()

    def _get_default_services(self) -> List[Dict[str, Any]]:
        """Return default service list."""
        return [
            {
                'name': 'api-gateway',
                'current_version': 'v1.2.3',
                'status': 'running'
            },
            {
                'name': 'user-service',
                'current_version': 'v2.1.0',
                'status': 'running'
            },
            {
                'name': 'payment-service',
                'current_version': 'v1.5.2',
                'status': 'running'
            },
            {
                'name': 'notification-service',
                'current_version': 'v1.0.8',
                'status': 'running'
            },
            {
                'name': 'analytics-service',
                'current_version': 'v0.9.1',
                'status': 'stopped'
            }
        ]

    def validate_deployment_request(
        self,
        services: List[str],
        branch: str
    ) -> tuple[bool, str]:
        """Validate deployment request."""
        if not services:
            return False, "No services specified"

        if not branch or not branch.strip():
            return False, "Branch name is required"

        available_services = [s['name'] for s in self.get_available_services()]
        invalid_services = [s for s in services if s not in available_services]

        if invalid_services:
            return False, f"Invalid services: {', '.join(invalid_services)}"

        return True, ""

    def trigger_deployment(
        self,
        services: List[str],
        branch: str,
        environment: str = 'uat'
    ) -> Dict[str, Any]:
        """Trigger deployment for selected services."""
        deployment_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        deployment_request = {
            'deployment_id': deployment_id,
            'environment': environment,
            'services': services,
            'branch': branch,
            'timestamp': timestamp,
            'triggered_by': 'manual'
        }

        logger.info(
            f"Triggering UAT deployment {deployment_id} "
            f"for services: {', '.join(services)} from branch: {branch}"
        )

        # In production, this would make an actual API call to the deployment service
        # For now, we log and return success
        try:
            # Here you would implement the actual deployment trigger
            # Example:
            # response = requests.post(
            #     self.deployment_endpoint,
            #     json=deployment_request,
            #     headers={'Authorization': f'Bearer {get_auth_token()}'}
            # )
            # response.raise_for_status()
            # return response.json()

            return {
                'deployment_id': deployment_id,
                'status': 'initiated',
                'services': services,
                'branch': branch,
                'environment': environment,
                'message': f'Successfully initiated deployment for {len(services)} service(s)'
            }
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            raise


def get_services_handler(request) -> tuple[Dict[str, Any], int]:
    """Handler for GET /api/uat/services."""
    try:
        service = UATDeploymentService()
        services = service.get_available_services()
        return {'services': services}, 200
    except Exception as e:
        logger.error(f"Failed to fetch services: {e}")
        return {'error': 'Failed to fetch services'}, 500


def deploy_handler(request) -> tuple[Dict[str, Any], int]:
    """Handler for POST /api/uat/deploy."""
    try:
        data = request.get_json()
        services = data.get('services', [])
        branch = data.get('branch', 'main')
        environment = data.get('environment', 'uat')

        service = UATDeploymentService()
        is_valid, error_message = service.validate_deployment_request(
            services, branch
        )

        if not is_valid:
            return {'error': error_message}, 400

        result = service.trigger_deployment(services, branch, environment)
        return result, 200

    except Exception as e:
        logger.error(f"Deployment request failed: {e}")
        return {'error': 'Deployment failed'}, 500
