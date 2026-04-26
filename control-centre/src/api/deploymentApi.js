const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

export const triggerUATDeployment = async (deploymentConfig) => {
  try {
    const response = await fetch(`${API_BASE_URL}/deployments/uat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
      },
      body: JSON.stringify(deploymentConfig),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `Deployment failed with status ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error triggering UAT deployment:', error);
    throw error;
  }
};

export const getDeploymentStatus = async (deploymentId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/deployments/${deploymentId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch deployment status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching deployment status:', error);
    throw error;
  }
};

export const getDeploymentHistory = async (environment = 'uat', limit = 10) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/deployments/history?environment=${environment}&limit=${limit}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch deployment history: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching deployment history:', error);
    throw error;
  }
};

export const cancelDeployment = async (deploymentId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/deployments/${deploymentId}/cancel`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to cancel deployment: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error cancelling deployment:', error);
    throw error;
  }
};