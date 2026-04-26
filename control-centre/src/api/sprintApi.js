const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

export const triggerSprint = async (sprintData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/sprints/trigger`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify(sprintData)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to trigger sprint');
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
};

export const getActiveSprints = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/sprints/active`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to fetch active sprints');
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
};

export const endSprint = async (sprintId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/sprints/${sprintId}/end`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to end sprint');
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
};
