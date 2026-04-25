"""Auto-review API handlers."""

import os
import requests
from typing import List, Dict, Any


class ReviewAPIError(Exception):
    """Custom exception for Review API errors."""
    pass


def get_api_base_url() -> str:
    """Get the API base URL from environment."""
    return os.getenv('SPRINT_API_BASE_URL', 'http://localhost:8000')


def get_auth_token() -> str:
    """Get authentication token from environment."""
    token = os.getenv('SPRINT_API_TOKEN')
    if not token:
        raise ReviewAPIError('SPRINT_API_TOKEN environment variable not set')
    return token


def fetch_pr_reviews(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch recent PR reviews.
    
    Args:
        limit: Maximum number of reviews to fetch
        
    Returns:
        List of PR review dictionaries
        
    Raises:
        ReviewAPIError: If the API request fails
    """
    url = f"{get_api_base_url()}/api/v1/reviews"
    headers = {
        'Authorization': f'Bearer {get_auth_token()}',
    }
    params = {'limit': limit}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json().get('reviews', [])
    except requests.exceptions.RequestException as e:
        raise ReviewAPIError(f'Failed to fetch PR reviews: {str(e)}')


def trigger_pr_review(pr_number: int) -> Dict[str, Any]:
    """
    Trigger an auto-review for a specific PR.
    
    Args:
        pr_number: The pull request number
        
    Returns:
        Dict containing review trigger information
        
    Raises:
        ReviewAPIError: If the API request fails
    """
    url = f"{get_api_base_url()}/api/v1/reviews/trigger"
    headers = {
        'Authorization': f'Bearer {get_auth_token()}',
        'Content-Type': 'application/json'
    }
    payload = {'pr_number': pr_number}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ReviewAPIError(f'Failed to trigger PR review: {str(e)}')


def get_review_details(pr_number: int) -> Dict[str, Any]:
    """
    Get detailed review information for a PR.
    
    Args:
        pr_number: The pull request number
        
    Returns:
        Dict containing detailed review information
        
    Raises:
        ReviewAPIError: If the API request fails
    """
    url = f"{get_api_base_url()}/api/v1/reviews/{pr_number}"
    headers = {
        'Authorization': f'Bearer {get_auth_token()}',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ReviewAPIError(f'Failed to get review details: {str(e)}')
