from flask import Blueprint, request, jsonify
from functools import wraps
import logging
from .pm_agent_handler import PMAgentHandler

logger = logging.getLogger(__name__)
pm_agent_bp = Blueprint('pm_agent', __name__, url_prefix='/api/pm-agent')

# Initialize handler
try:
    pm_handler = PMAgentHandler()
except Exception as e:
    logger.error(f"Failed to initialize PMAgentHandler: {e}")
    pm_handler = None


def require_auth(f):
    """Simple auth decorator - integrate with your auth system."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # TODO: Implement actual authentication check
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function


@pm_agent_bp.route('/chat', methods=['POST'])
@require_auth
def chat():
    """Handle PM Agent chat messages."""
    if not pm_handler:
        return jsonify({
            "error": "PM Agent service not available"
        }), 503

    try:
        data = request.get_json()
        project_id = data.get('project_id')
        message = data.get('message')
        conversation_history = data.get('conversation_history', [])

        if not project_id or not message:
            return jsonify({
                "error": "project_id and message are required"
            }), 400

        # Optional: Fetch backlog data for context
        backlog_data = _fetch_backlog_data(project_id)

        result = pm_handler.process_chat_message(
            project_id=project_id,
            message=message,
            conversation_history=conversation_history,
            backlog_data=backlog_data
        )

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return jsonify({
            "error": "Failed to process message",
            "details": str(e)
        }), 500


@pm_agent_bp.route('/approve-sprint', methods=['POST'])
@require_auth
def approve_sprint():
    """Approve or reject a sprint plan."""
    if not pm_handler:
        return jsonify({
            "error": "PM Agent service not available"
        }), 503

    try:
        data = request.get_json()
        project_id = data.get('project_id')
        sprint_plan = data.get('sprint_plan')
        approved = data.get('approved', False)

        if not project_id or not sprint_plan:
            return jsonify({
                "error": "project_id and sprint_plan are required"
            }), 400

        if approved:
            sprint = pm_handler.create_sprint_from_plan(
                project_id=project_id,
                sprint_plan=sprint_plan
            )
            
            # TODO: Persist sprint to database
            logger.info(f"Sprint created: {sprint['id']} for project {project_id}")
            
            return jsonify({
                "success": True,
                "sprint": sprint
            }), 200
        else:
            return jsonify({
                "success": True,
                "message": "Sprint plan rejected"
            }), 200

    except Exception as e:
        logger.error(f"Approval error: {e}", exc_info=True)
        return jsonify({
            "error": "Failed to process approval",
            "details": str(e)
        }), 500


@pm_agent_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy" if pm_handler else "degraded",
        "service": "pm-agent"
    }), 200


def _fetch_backlog_data(project_id: str):
    """Fetch backlog data for context (stub implementation)."""
    # TODO: Implement actual backlog data fetching
    return {
        "items": [],
        "unestimated_count": 0,
        "avg_velocity": 30
    }


def register_routes(app):
    """Register PM Agent routes with Flask app."""
    app.register_blueprint(pm_agent_bp)