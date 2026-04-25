"""Flask routes for SonarCloud operations."""

from flask import Blueprint, request, jsonify
from .sonarcloud_helper import SonarCloudHelper
import os

sonarcloud_bp = Blueprint('sonarcloud', __name__, url_prefix='/api/sonarcloud')


def get_sonarcloud_helper():
    """Get configured SonarCloud helper instance."""
    return SonarCloudHelper(
        token=os.getenv('SONARCLOUD_TOKEN'),
        organization=os.getenv('SONARCLOUD_ORG')
    )


@sonarcloud_bp.route('/trigger', methods=['POST'])
def trigger_analysis():
    """Trigger SonarCloud analysis for a repository.
    
    Expected JSON payload:
    {
        "repository": "owner/repo-name",
        "branch": "main"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        repository = data.get('repository')
        branch = data.get('branch', 'main')
        
        if not repository:
            return jsonify({'error': 'Repository is required'}), 400
        
        helper = get_sonarcloud_helper()
        result = helper.trigger_analysis(repository, branch)
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to trigger analysis: {str(e)}'}), 500


@sonarcloud_bp.route('/results', methods=['GET'])
def get_results():
    """Get SonarCloud analysis results for a repository.
    
    Query parameters:
        repository: Repository name in format 'owner/repo'
    """
    try:
        repository = request.args.get('repository')
        
        if not repository:
            return jsonify({'error': 'Repository parameter is required'}), 400
        
        helper = get_sonarcloud_helper()
        results = helper.get_full_analysis(repository)
        
        return jsonify(results), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to fetch results: {str(e)}'}), 500


@sonarcloud_bp.route('/status/<path:repository>', methods=['GET'])
def get_status(repository):
    """Get quality gate status for a repository.
    
    Args:
        repository: Repository name in format 'owner/repo'
    """
    try:
        helper = get_sonarcloud_helper()
        status = helper.get_project_status(repository)
        
        return jsonify(status), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to fetch status: {str(e)}'}), 500


@sonarcloud_bp.route('/issues/<path:repository>', methods=['GET'])
def get_issues(repository):
    """Get open issues for a repository.
    
    Args:
        repository: Repository name in format 'owner/repo'
        
    Query parameters:
        page_size: Number of issues to return (default: 20)
    """
    try:
        page_size = request.args.get('page_size', 20, type=int)
        
        helper = get_sonarcloud_helper()
        issues = helper.get_project_issues(repository, page_size)
        
        return jsonify(issues), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to fetch issues: {str(e)}'}), 500
