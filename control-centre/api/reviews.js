/**
 * Auto-review API client for React frontend.
 */

const API_BASE_URL = process.env.REACT_APP_SPRINT_API_BASE_URL || 'http://localhost:8000';

/**
 * Get authorization headers for API requests.
 */
const getAuthHeaders = () => {
  const token = localStorage.getItem('sprint_api_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };
};

/**
 * Fetch recent PR reviews.
 * @param {number} limit - Maximum number of reviews to fetch
 * @returns {Promise<Array>} List of PR reviews
 */
export const fetchPRReviews = async (limit = 50) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/reviews?limit=${limit}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to fetch PR reviews' }));
    throw new Error(error.message || `HTTP ${response.status}`);
  }

  const data = await response.json();
  return data.reviews || [];
};

/**
 * Trigger an auto-review for a specific PR.
 * @param {number} prNumber - The pull request number
 * @returns {Promise<Object>} Review trigger information
 */
export const triggerPRReview = async (prNumber) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/reviews/trigger`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ pr_number: prNumber }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to trigger PR review' }));
    throw new Error(error.message || `HTTP ${response.status}`);
  }

  return response.json();
};

/**
 * Get detailed review information for a PR.
 * @param {number} prNumber - The pull request number
 * @returns {Promise<Object>} Detailed review information
 */
export const getReviewDetails = async (prNumber) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/reviews/${prNumber}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to get review details' }));
    throw new Error(error.message || `HTTP ${response.status}`);
  }

  return response.json();
};
