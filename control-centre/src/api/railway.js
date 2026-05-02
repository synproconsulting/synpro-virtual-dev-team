/**
 * Railway API client for the Control Centre frontend.
 * 
 * Provides functions to interact with Railway deployment data
 * through the backend API proxy.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Get all Railway projects accessible to the configured API token.
 * 
 * @returns {Promise<Object>} Projects data
 */
export const getRailwayProjects = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/railway/projects`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to fetch projects: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching Railway projects:', error);
    throw error;
  }
};

/**
 * Get all services in a Railway project.
 * 
 * @param {string} projectId - Railway project ID
 * @returns {Promise<Object>} Services data
 */
export const getRailwayServices = async (projectId) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/railway/projects/${projectId}/services`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to fetch services: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching Railway services:', error);
    throw error;
  }
};

/**
 * Get recent deployments for a service.
 * 
 * @param {string} serviceId - Railway service ID
 * @param {Object} options - Query options
 * @param {string} options.environmentId - Optional environment ID filter
 * @param {number} options.limit - Maximum deployments to return (default: 10)
 * @returns {Promise<Object>} Deployments data
 */
export const getServiceDeployments = async (serviceId, options = {}) => {
  try {
    const params = new URLSearchParams();
    if (options.environmentId) {
      params.append('environment_id', options.environmentId);
    }
    if (options.limit) {
      params.append('limit', options.limit.toString());
    }

    const url = `${API_BASE_URL}/api/railway/services/${serviceId}/deployments${
      params.toString() ? `?${params.toString()}` : ''
    }`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to fetch deployments: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching service deployments:', error);
    throw error;
  }
};

/**
 * Get all deployments for all services in a specific environment.
 * 
 * @param {string} projectId - Railway project ID
 * @param {string} environmentName - Environment name (e.g., 'production', 'staging', 'uat')
 * @returns {Promise<Object>} Environment deployments data
 */
export const getEnvironmentDeployments = async (projectId, environmentName = 'production') => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/railway/projects/${projectId}/environments/${environmentName}/deployments`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `Failed to fetch environment deployments: ${response.status}`
      );
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching environment deployments:', error);
    throw error;
  }
};

/**
 * Get logs for a specific deployment.
 * 
 * @param {string} deploymentId - Railway deployment ID
 * @param {number} limit - Maximum log entries to return (default: 100)
 * @returns {Promise<Object>} Deployment logs data
 */
export const getDeploymentLogs = async (deploymentId, limit = 100) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/railway/deployments/${deploymentId}/logs?limit=${limit}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to fetch logs: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching deployment logs:', error);
    throw error;
  }
};

/**
 * Trigger a new deployment for a service.
 * 
 * @param {string} serviceId - Railway service ID
 * @param {string} environmentId - Railway environment ID
 * @returns {Promise<Object>} Triggered deployment data
 */
export const triggerDeployment = async (serviceId, environmentId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/railway/deployments/trigger`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        service_id: serviceId,
        environment_id: environmentId,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to trigger deployment: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error triggering deployment:', error);
    throw error;
  }
};

/**
 * Check Railway API health and configuration status.
 * 
 * @returns {Promise<Object>} Health status
 */
export const checkRailwayHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/railway/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error checking Railway health:', error);
    throw error;
  }
};

/**
 * Format Railway deployment status for display.
 * 
 * @param {string} status - Railway deployment status
 * @returns {Object} Formatted status with color and label
 */
export const formatDeploymentStatus = (status) => {
  const statusMap = {
    SUCCESS: { label: 'Success', color: '#22c55e' },
    FAILED: { label: 'Failed', color: '#ef4444' },
    BUILDING: { label: 'Building', color: '#3b82f6' },
    DEPLOYING: { label: 'Deploying', color: '#8b5cf6' },
    CRASHED: { label: 'Crashed', color: '#dc2626' },
    REMOVED: { label: 'Removed', color: '#6b7280' },
    REMOVING: { label: 'Removing', color: '#9ca3af' },
    INITIALIZING: { label: 'Initializing', color: '#06b6d4' },
    WAITING: { label: 'Waiting', color: '#f59e0b' },
    ACTIVE: { label: 'Active', color: '#10b981' },
  };

  return statusMap[status] || { label: status, color: '#6b7280' };
};
