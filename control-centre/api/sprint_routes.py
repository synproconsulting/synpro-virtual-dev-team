"""Flask routes for sprint status endpoints."""
from flask import Blueprint, jsonify, request
from control_centre.api.sprint_status import fetch_sprint_status

sprint_bp = Blueprint('sprint', __name__, url_prefix='/api/sprint')


@sprint_bp.route('/<sprint_id>/status', methods=['GET'])
def get_sprint_status(sprint_id):
    """Get complete sprint status including Jira, PRs, and CI builds."""
    try:
        data = fetch_sprint_status(sprint_id)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sprint_bp.route('/active', methods=['GET'])
def get_active_sprints():
    """Get list of active sprints."""
    # This would typically query Jira for active sprints
    # Placeholder implementation
    return jsonify({
        'sprints': [
            {'id': '123', 'name': 'Sprint 45', 'state': 'active'},
        ]
    }), 200
