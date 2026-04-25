/**
 * Sprint trigger API client for React frontend.
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
 * Trigger a new sprint execution.
 * @returns {Promise<Object>} Sprint run information
 */
export const triggerSprint = async () => {
  const response = await fetch(`${API_BASE_URL}/api/v1/sprint/trigger`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to trigger sprint' }));
    throw new Error(error.message || `HTTP ${response.status}`);
  }

  return response.json();
};

/**
 * Get the status of a sprint run.
 * @param {string} runId - The sprint run identifier
 * @returns {Promise<Object>} Sprint status information
 */
export const getSprintStatus = async (runId) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/sprint/${runId}/status`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Failed to get sprint status' }));
    throw new Error(error.message || `HTTP ${response.status}`);
  }

  return response.json();
};
