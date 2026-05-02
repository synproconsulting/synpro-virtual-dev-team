/**
 * railwayApi.js
 * =============
 * API client for Railway deployment operations via the backend proxy.
 * SDT1-58: Wire UAT Deploy tab to Railway GraphQL API
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Get authentication token from localStorage
 */
const getAuthToken = () => {
  return localStorage.getItem('authToken');
};

/**
 * Get all Railway projects
 */
export const getRailwayProjects = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/railway/projects`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`,
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
 * Get all services for a specific project
 */
export const getProjectServices = async (projectId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/railway/projects/${projectId}/services`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to fetch services: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching project services:', error);
    throw error;
  }
};

/**
 * Get all environments for a specific project
 */
export const getProjectEnvironments = async (projectId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/railway/projects/${projectId}/environments`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to fetch environments: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching project environments:', error);
    throw error;
  }
};

/**
 * Get deployment history for a service
 */
export const getServiceDeployments = async (serviceId, limit = 10) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/railway/services/${serviceId}/deployments?limit=${limit}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`,
        },
      }
    );

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
 * Trigger a new deployment
 */
export const triggerDeployment = async (serviceId, environmentId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/railway/deployments/trigger`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`,
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
 * Get deployment status
 */
export const getDeploymentStatus = async (deploymentId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/railway/deployments/${deploymentId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to fetch deployment status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching deployment status:', error);
    throw error;
  }
};

/**
 * Get environment variables for a service
 */
export const getServiceVariables = async (serviceId, environmentId) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/railway/services/${serviceId}/variables?environment_id=${environmentId}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`,
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to fetch service variables: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching service variables:', error);
    throw error;
  }
};

/**
 * Check Railway API health
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
      return { status: 'unhealthy', message: 'API not responding' };
    }

    return await response.json();
  } catch (error) {
    console.error('Error checking Railway health:', error);
    return { status: 'unhealthy', message: error.message };
  }
};
