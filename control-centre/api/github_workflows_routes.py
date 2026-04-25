"""Flask routes for GitHub workflows API endpoints."""
from flask import Blueprint, jsonify, request
from control_centre.api.github_workflows import GitHubWorkflowsAPI
import os

# Create blueprint for GitHub workflows routes
github_bp = Blueprint('github', __name__, url_prefix='/api/github')


@github_bp.route('/workflows', methods=['GET'])
def get_workflows():
    """Get workflow runs for a repository.
    
    Query params:
        owner: Repository owner (required)
        repo: Repository name (required)
        per_page: Number of results (default: 10, max: 100)
        status: Filter by status (optional)
    """
    owner = request.args.get('owner')
    repo = request.args.get('repo')
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    
    if not owner or not repo:
        return jsonify({'error': 'owner and repo parameters are required'}), 400
    
    try:
        api = GitHubWorkflowsAPI()
        data = api.get_workflow_runs(owner, repo, per_page, status)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@github_bp.route('/workflows/summary', methods=['GET'])
def get_workflow_summary():
    """Get a summary of workflow statuses.
    
    Query params:
        owner: Repository owner (required)
        repo: Repository name (required)
    """
    owner = request.args.get('owner')
    repo = request.args.get('repo')
    
    if not owner or not repo:
        return jsonify({'error': 'owner and repo parameters are required'}), 400
    
    try:
        api = GitHubWorkflowsAPI()
        summary = api.get_workflow_status_summary(owner, repo)
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@github_bp.route('/workflows/<workflow_id>/latest', methods=['GET'])
def get_latest_workflow_run(workflow_id):
    """Get the latest run for a specific workflow.
    
    Path params:
        workflow_id: Workflow ID or filename
        
    Query params:
        owner: Repository owner (required)
        repo: Repository name (required)
    """
    owner = request.args.get('owner')
    repo = request.args.get('repo')
    
    if not owner or not repo:
        return jsonify({'error': 'owner and repo parameters are required'}), 400
    
    try:
        api = GitHubWorkflowsAPI()
        data = api.get_latest_run_for_workflow(owner, repo, workflow_id)
        if data:
            return jsonify(data), 200
        else:
            return jsonify({'error': 'No runs found for this workflow'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@github_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for GitHub API integration."""
    token_configured = bool(os.environ.get('GITHUB_TOKEN'))
    return jsonify({
        'status': 'ok',
        'token_configured': token_configured
    }), 200
