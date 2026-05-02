/**
 * Deployment API client for Railway integration
 * SDT1-58: UAT Deploy tab - wire to Railway GraphQL API
 */

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

/**
 * Get list of available services from Railway
 */
export const getServices = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/deployments/services`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to fetch services: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching services:', error);
    throw error;
  }
};

/**
 * Get list of available environments from Railway
 */
export const getEnvironments = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/deployments/environments`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to fetch environments: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching environments:', error);
    throw error;
  }
};

/**
 * Trigger a new deployment via Railway
 */
export const triggerDeployment = async (serviceId, environmentId = null, customBranch = null, notes = null) => {
  try {
    const payload = {
      service_id: serviceId,
      environment_id: environmentId,
      custom_branch: customBranch,
      notes: notes,
    };

    const response = await fetch(`${API_BASE_URL}/api/deployments/trigger`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Deployment failed with status ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error triggering deployment:', error);
    throw error;
  }
};

/**
 * Get deployment status by ID
 */
export const getDeploymentStatus = async (deploymentId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/deployments/${deploymentId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
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
 * Get deployments for a specific service
 */
export const getServiceDeployments = async (serviceId, limit = 10) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/deployments/service/${serviceId}/deployments?limit=${limit}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to fetch service deployments: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching service deployments:', error);
    throw error;
  }
};

/**
 * Get deployment logs
 */
export const getDeploymentLogs = async (deploymentId, limit = 100) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/deployments/${deploymentId}/logs?limit=${limit}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to fetch deployment logs: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching deployment logs:', error);
    throw error;
  }
};

// Legacy compatibility functions (for existing code that might use these)
export const triggerUATDeployment = async (deploymentConfig) => {
  // Map old API to new API
  const { services, branch, deploymentNotes } = deploymentConfig;
  
  if (!services || services.length === 0) {
    throw new Error('At least one service must be selected');
  }
  
  // Trigger deployment for each selected service
  const results = await Promise.all(
    services.map(serviceId => 
      triggerDeployment(serviceId, null, branch, deploymentNotes)
    )
  );
  
  return {
    deploymentId: results[0]?.deployment_id,
    status: 'triggered',
    services: results.length,
    results: results,
  };
};

export const getDeploymentHistory = async (environment = 'uat', limit = 10) => {
  // For now, this would need to be implemented if we want to show
  // deployment history across all services
  console.warn('getDeploymentHistory not yet implemented for Railway integration');
  return { deployments: [], total: 0 };
};

export const cancelDeployment = async (deploymentId) => {
  // Railway doesn't support cancelling deployments via API currently
  console.warn('cancelDeployment not supported for Railway deployments');
  throw new Error('Deployment cancellation is not supported');
};
