"""Flask routes for GitHub Actions integration."""
from flask import Blueprint, request, jsonify
from control-centre.api.github_workflows import GitHubWorkflowsAPI

github_bp = Blueprint('github', __name__, url_prefix='/api/github')


@github_bp.route('/workflows', methods=['GET'])
def get_workflows():
    """Get workflow runs for a repository.
    
    Query params:
        owner: Repository owner (required)
        repo: Repository name (required)
        branch: Branch filter (optional)
        status: Status filter (optional)
        per_page: Results per page, default 10 (optional)
    """
    owner = request.args.get('owner')
    repo = request.args.get('repo')
    
    if not owner or not repo:
        return jsonify({
            'error': 'Missing required parameters: owner and repo'
        }), 400
    
    branch = request.args.get('branch')
    status = request.args.get('status')
    per_page = request.args.get('per_page', 10, type=int)
    
    api = GitHubWorkflowsAPI()
    result = api.get_workflow_runs(
        owner=owner,
        repo=repo,
        branch=branch,
        status=status,
        per_page=per_page
    )
    
    if not result['success']:
        return jsonify({
            'error': result.get('error', 'Failed to fetch workflows')
        }), 500
    
    return jsonify(result)


@github_bp.route('/workflows/<int:run_id>', methods=['GET'])
def get_workflow_details(run_id):
    """Get details for a specific workflow run.
    
    Query params:
        owner: Repository owner (required)
        repo: Repository name (required)
    """
    owner = request.args.get('owner')
    repo = request.args.get('repo')
    
    if not owner or not repo:
        return jsonify({
            'error': 'Missing required parameters: owner and repo'
        }), 400
    
    api = GitHubWorkflowsAPI()
    result = api.get_workflow_run_details(owner=owner, repo=repo, run_id=run_id)
    
    if not result['success']:
        return jsonify({
            'error': result.get('error', 'Failed to fetch workflow details')
        }), 500
    
    return jsonify(result)


@github_bp.route('/workflows/<int:run_id>/jobs', methods=['GET'])
def get_workflow_jobs(run_id):
    """Get jobs for a specific workflow run.
    
    Query params:
        owner: Repository owner (required)
        repo: Repository name (required)
    """
    owner = request.args.get('owner')
    repo = request.args.get('repo')
    
    if not owner or not repo:
        return jsonify({
            'error': 'Missing required parameters: owner and repo'
        }), 400
    
    api = GitHubWorkflowsAPI()
    result = api.get_workflow_jobs(owner=owner, repo=repo, run_id=run_id)
    
    if not result['success']:
        return jsonify({
            'error': result.get('error', 'Failed to fetch workflow jobs')
        }), 500
    
    return jsonify(result)


@github_bp.route('/repository/workflows', methods=['GET'])
def get_repository_workflows():
    """Get all workflow definitions for a repository.
    
    Query params:
        owner: Repository owner (required)
        repo: Repository name (required)
    """
    owner = request.args.get('owner')
    repo = request.args.get('repo')
    
    if not owner or not repo:
        return jsonify({
            'error': 'Missing required parameters: owner and repo'
        }), 400
    
    api = GitHubWorkflowsAPI()
    result = api.get_repository_workflows(owner=owner, repo=repo)
    
    if not result['success']:
        return jsonify({
            'error': result.get('error', 'Failed to fetch repository workflows')
        }), 500
    
    return jsonify(result)
