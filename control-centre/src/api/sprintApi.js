const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '/api';

const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.message || `HTTP ${response.status}`);
  }
  return response.json();
};

const getAuthHeaders = () => {
  const token = localStorage.getItem('authToken');
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` })
  };
};

export const fetchSprintData = async (sprintId) => {
  const response = await fetch(`${API_BASE_URL}/sprints/${sprintId}`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

export const fetchJiraIssues = async (sprintId) => {
  const response = await fetch(`${API_BASE_URL}/sprints/${sprintId}/jira`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

export const fetchPullRequests = async (sprintId) => {
  const response = await fetch(`${API_BASE_URL}/sprints/${sprintId}/pull-requests`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

export const fetchCIPipelines = async (sprintId) => {
  const response = await fetch(`${API_BASE_URL}/sprints/${sprintId}/ci-pipelines`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

export const fetchSprintMetrics = async (sprintId) => {
  const response = await fetch(`${API_BASE_URL}/sprints/${sprintId}/metrics`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

export const refreshSprintData = async (sprintId) => {
  const response = await fetch(`${API_BASE_URL}/sprints/${sprintId}/refresh`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};