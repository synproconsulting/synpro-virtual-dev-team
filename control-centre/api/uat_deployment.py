"""UAT deployment API endpoints."""
import os
import json
from datetime import datetime
from typing import List, Dict, Any
from flask import Blueprint, request, jsonify
from functools import wraps

uat_bp = Blueprint('uat', __name__, url_prefix='/api/uat')


def get_config(key: str, default: Any = None) -> Any:
    """Get configuration from environment variables."""
    return os.environ.get(key, default)


def require_auth(f):
    """Decorator to require authentication for endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Authentication should be handled by the main app middleware
        # This is a placeholder for the decorator
        return f(*args, **kwargs)
    return decorated_function


class UATDeploymentService:
    """Service for managing UAT deployments."""
    
    def __init__(self):
        self.deployment_api_url = get_config('UAT_DEPLOYMENT_API_URL')
        self.services_config_path = get_config('SERVICES_CONFIG_PATH', 'config/services.json')
    
    def get_available_services(self) -> List[Dict[str, Any]]:
        """Get list of available services for deployment."""
        # In production, this would fetch from a service registry or config
        return [
            {
                'id': 'api-gateway',
                'name': 'API Gateway',
                'version': '2.3.1',
                'status': 'active'
            },
            {
                'id': 'user-service',
                'name': 'User Service',
                'version': '1.8.4',
                'status': 'active'
            },
            {
                'id': 'payment-service',
                'name': 'Payment Service',
                'version': '3.1.0',
                'status': 'active'
            },
            {
                'id': 'notification-service',
                'name': 'Notification Service',
                'version': '1.5.2',
                'status': 'active'
            },
            {
                'id': 'analytics-service',
                'name': 'Analytics Service',
                'version': '2.0.1',
                'status': 'inactive'
            }
        ]
    
    def deploy_services(self, service_ids: List[str], user: str) -> Dict[str, Any]:
        """Deploy selected services to UAT environment."""
        # In production, this would trigger actual deployment pipeline
        deployment_id = f"DEP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Simulate deployment
        services = self.get_available_services()
        selected_services = [s for s in services if s['id'] in service_ids]
        
        if not selected_services:
            raise ValueError('No valid services selected')
        
        deployment_record = {
            'id': deployment_id,
            'services': [s['name'] for s in selected_services],
            'service_ids': service_ids,
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'user': user
        }
        
        # Store deployment record
        self._store_deployment(deployment_record)
        
        return {
            'deployment_id': deployment_id,
            'status': 'success',
            'message': f'Successfully deployed {len(selected_services)} service(s) to UAT',
            'services': [s['name'] for s in selected_services]
        }
    
    def get_deployment_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent deployment history."""
        # In production, this would fetch from a database
        return [
            {
                'id': 'DEP-20240115120000',
                'services': ['API Gateway', 'User Service'],
                'status': 'success',
                'timestamp': '2024-01-15T12:00:00Z',
                'user': 'admin@example.com'
            },
            {
                'id': 'DEP-20240115100000',
                'services': ['Payment Service'],
                'status': 'success',
                'timestamp': '2024-01-15T10:00:00Z',
                'user': 'devops@example.com'
            },
            {
                'id': 'DEP-20240114180000',
                'services': ['Notification Service', 'Analytics Service'],
                'status': 'failed',
                'timestamp': '2024-01-14T18:00:00Z',
                'user': 'admin@example.com'
            }
        ]
    
    def _store_deployment(self, deployment: Dict[str, Any]) -> None:
        """Store deployment record."""
        # In production, this would save to a database
        pass


deployment_service = UATDeploymentService()


@uat_bp.route('/services', methods=['GET'])
@require_auth
def get_services():
    """Get available services for UAT deployment."""
    try:
        services = deployment_service.get_available_services()
        return jsonify({'services': services}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@uat_bp.route('/deploy', methods=['POST'])
@require_auth
def deploy():
    """Deploy selected services to UAT environment."""
    try:
        data = request.get_json()
        service_ids = data.get('service_ids', [])
        
        if not service_ids:
            return jsonify({'error': 'No services selected'}), 400
        
        # Get user from request context (set by auth middleware)
        user = request.headers.get('X-User-Email', 'unknown@example.com')
        
        result = deployment_service.deploy_services(service_ids, user)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@uat_bp.route('/deployments/history', methods=['GET'])
@require_auth
def get_deployment_history():
    """Get deployment history."""
    try:
        limit = request.args.get('limit', 50, type=int)
        deployments = deployment_service.get_deployment_history(limit)
        return jsonify({'deployments': deployments}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def register_blueprint(app):
    """Register UAT deployment blueprint with Flask app."""
    app.register_blueprint(uat_bp)