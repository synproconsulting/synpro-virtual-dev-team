/**
 * Railway API client for UAT deployments.
 * Communicates with the backend API which interfaces with Railway GraphQL API.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Get authorization token from localStorage
 */
const getAuthToken = () => {
  return localStorage.getItem('authToken') || '';
};

/**
 * Make an authenticated API request
 */
const apiRequest = async (endpoint, options = {}) => {
  const token = getAuthToken();
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Request failed with status ${response.status}`);
  }
  
  return response.json();
};

/**
 * List all available services in the Railway project
 */
export const listServices = async () => {
  try {
    return await apiRequest('/api/deployments/services');
  } catch (error) {
    console.error('Error listing services:', error);
    throw error;
  }
};

/**
 * List all available environments in the Railway project
 */
export const listEnvironments = async () => {
  try {
    return await apiRequest('/api/deployments/environments');
  } catch (error) {
    console.error('Error listing environments:', error);
    throw error;
  }
};

/**
 * Trigger deployment for one or more services
 * 
 * @param {Object} config - Deployment configuration
 * @param {string[]} config.service_ids - Array of service IDs to deploy
 * @param {string} [config.environment_id] - Environment ID (optional)
 * @param {string} [config.deployment_notes] - Optional deployment notes
 */
export const triggerDeployment = async (config) => {
  try {
    return await apiRequest('/api/deployments/trigger', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  } catch (error) {
    console.error('Error triggering deployment:', error);
    throw error;
  }
};

/**
 * Get the status of a specific deployment
 * 
 * @param {string} deploymentId - Railway deployment ID
 */
export const getDeploymentStatus = async (deploymentId) => {
  try {
    return await apiRequest(`/api/deployments/status/${deploymentId}`);
  } catch (error) {
    console.error('Error getting deployment status:', error);
    throw error;
  }
};

/**
 * Get deployment history
 * 
 * @param {Object} options - Query options
 * @param {string} [options.service_id] - Filter by service ID
 * @param {number} [options.limit=10] - Maximum number of deployments to return
 */
export const getDeploymentHistory = async (options = {}) => {
  try {
    const params = new URLSearchParams();
    if (options.service_id) {
      params.append('service_id', options.service_id);
    }
    if (options.limit) {
      params.append('limit', options.limit.toString());
    }
    
    const query = params.toString() ? `?${params.toString()}` : '';
    return await apiRequest(`/api/deployments/history${query}`);
  } catch (error) {
    console.error('Error getting deployment history:', error);
    throw error;
  }
};

/**
 * Get logs for a deployment
 * 
 * @param {string} deploymentId - Railway deployment ID
 * @param {number} [limit=100] - Maximum number of log lines to return
 */
export const getDeploymentLogs = async (deploymentId, limit = 100) => {
  try {
    return await apiRequest(`/api/deployments/logs/${deploymentId}?limit=${limit}`);
  } catch (error) {
    console.error('Error getting deployment logs:', error);
    throw error;
  }
};

/**
 * Poll deployment status until it reaches a terminal state
 * 
 * @param {string} deploymentId - Railway deployment ID
 * @param {Function} onUpdate - Callback function called on each status update
 * @param {number} [interval=5000] - Polling interval in milliseconds
 * @param {number} [timeout=600000] - Timeout in milliseconds (default: 10 minutes)
 */
export const pollDeploymentStatus = async (
  deploymentId,
  onUpdate,
  interval = 5000,
  timeout = 600000
) => {
  const startTime = Date.now();
  const terminalStates = ['SUCCESS', 'FAILED', 'CRASHED', 'REMOVED'];
  
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const status = await getDeploymentStatus(deploymentId);
        
        if (onUpdate) {
          onUpdate(status);
        }
        
        // Check if deployment reached terminal state
        if (terminalStates.includes(status.status)) {
          resolve(status);
          return;
        }
        
        // Check timeout
        if (Date.now() - startTime > timeout) {
          reject(new Error('Deployment status polling timed out'));
          return;
        }
        
        // Continue polling
        setTimeout(poll, interval);
      } catch (error) {
        reject(error);
      }
    };
    
    poll();
  });
};
