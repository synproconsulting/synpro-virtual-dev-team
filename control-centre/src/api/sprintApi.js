const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

export const fetchSprintData = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/sprint/current`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching sprint data:', error);
    throw error;
  }
};

export const fetchJiraIssues = async (sprintId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/jira/sprint/${sprintId}/issues`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching Jira issues:', error);
    throw error;
  }
};

export const fetchPullRequests = async (filters = {}) => {
  const params = new URLSearchParams(filters);
  try {
    const response = await fetch(`${API_BASE_URL}/github/prs?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching pull requests:', error);
    throw error;
  }
};

export const fetchCIPipelines = async (filters = {}) => {
  const params = new URLSearchParams(filters);
  try {
    const response = await fetch(`${API_BASE_URL}/ci/pipelines?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching CI pipelines:', error);
    throw error;
  }
};

export const refreshSprintData = async (sprintId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/sprint/${sprintId}/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error refreshing sprint data:', error);
    throw error;
  }
};