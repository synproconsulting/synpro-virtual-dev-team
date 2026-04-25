"""Sprint trigger API handlers."""

import os
import requests
from typing import Dict, Any


class SprintAPIError(Exception):
    """Custom exception for Sprint API errors."""
    pass


def get_api_base_url() -> str:
    """Get the API base URL from environment."""
    return os.getenv('SPRINT_API_BASE_URL', 'http://localhost:8000')


def get_auth_token() -> str:
    """Get authentication token from environment."""
    token = os.getenv('SPRINT_API_TOKEN')
    if not token:
        raise SprintAPIError('SPRINT_API_TOKEN environment variable not set')
    return token


def trigger_sprint() -> Dict[str, Any]:
    """
    Trigger a new sprint execution.
    
    Returns:
        Dict containing run_id and status information
        
    Raises:
        SprintAPIError: If the API request fails
    """
    url = f"{get_api_base_url()}/api/v1/sprint/trigger"
    headers = {
        'Authorization': f'Bearer {get_auth_token()}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise SprintAPIError(f'Failed to trigger sprint: {str(e)}')


def get_sprint_status(run_id: str) -> Dict[str, Any]:
    """
    Get the status of a sprint run.
    
    Args:
        run_id: The sprint run identifier
        
    Returns:
        Dict containing sprint status information
        
    Raises:
        SprintAPIError: If the API request fails
    """
    url = f"{get_api_base_url()}/api/v1/sprint/{run_id}/status"
    headers = {
        'Authorization': f'Bearer {get_auth_token()}',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise SprintAPIError(f'Failed to get sprint status: {str(e)}')
