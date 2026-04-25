"""Flask routes for SonarCloud integration."""

from flask import Blueprint, jsonify, request, current_app
from .sonarcloud import get_client, SonarCloudAPIError

sonarcloud_bp = Blueprint('sonarcloud', __name__, url_prefix='/api/sonarcloud')


@sonarcloud_bp.route('/trigger', methods=['POST'])
def trigger_analysis():
    """Trigger SonarCloud analysis for a project."""
    try:
        data = request.get_json()
        project_key = data.get('projectKey')
        branch = data.get('branch', 'main')

        if not project_key:
            return jsonify({'error': 'projectKey is required'}), 400

        client = get_client()
        result = client.trigger_analysis(project_key, branch)

        return jsonify(result), 200

    except SonarCloudAPIError as e:
        current_app.logger.error(f"SonarCloud API error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@sonarcloud_bp.route('/status/<task_id>', methods=['GET'])
def get_analysis_status(task_id):
    """Get analysis task status."""
    try:
        client = get_client()
        status = client.get_analysis_status(task_id)

        return jsonify(status), 200

    except SonarCloudAPIError as e:
        current_app.logger.error(f"SonarCloud API error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@sonarcloud_bp.route('/results/<project_key>', methods=['GET'])
def get_project_results(project_key):
    """Get comprehensive results for a project."""
    try:
        branch = request.args.get('branch', 'main')

        client = get_client()
        results = client.get_project_results(project_key, branch)

        return jsonify(results), 200

    except SonarCloudAPIError as e:
        current_app.logger.error(f"SonarCloud API error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@sonarcloud_bp.route('/quality-gate/<project_key>', methods=['GET'])
def get_quality_gate(project_key):
    """Get quality gate status for a project."""
    try:
        branch = request.args.get('branch', 'main')

        client = get_client()
        quality_gate = client.get_quality_gate_status(project_key, branch)

        return jsonify(quality_gate), 200

    except SonarCloudAPIError as e:
        current_app.logger.error(f"SonarCloud API error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
