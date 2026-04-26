const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export const triggerSprint = async (sprintConfig) => {
  const response = await fetch(`${API_BASE_URL}/api/sprints/trigger`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${process.env.REACT_APP_API_TOKEN || ''}`,
    },
    body: JSON.stringify(sprintConfig),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Failed to trigger sprint');
  }

  return response.json();
};

export const getSprintStatus = async (sprintId) => {
  const response = await fetch(`${API_BASE_URL}/api/sprints/${sprintId}/status`, {
    headers: {
      'Authorization': `Bearer ${process.env.REACT_APP_API_TOKEN || ''}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Failed to fetch sprint status');
  }

  return response.json();
};

export const getAllSprints = async () => {
  const response = await fetch(`${API_BASE_URL}/api/sprints`, {
    headers: {
      'Authorization': `Bearer ${process.env.REACT_APP_API_TOKEN || ''}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Failed to fetch sprints');
  }

  return response.json();
};
