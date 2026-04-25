/**
 * SonarCloud API client for frontend
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

class SonarCloudAPIError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'SonarCloudAPIError';
    this.status = status;
  }
}

const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new SonarCloudAPIError(
      error.error || `HTTP ${response.status}: ${response.statusText}`,
      response.status
    );
  }
  return response.json();
};

export const triggerSonarAnalysis = async (projectKey, branch = 'main') => {
  const response = await fetch(`${API_BASE_URL}/sonarcloud/trigger`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ projectKey, branch }),
  });

  return handleResponse(response);
};

export const fetchAnalysisStatus = async (taskId) => {
  const response = await fetch(`${API_BASE_URL}/sonarcloud/status/${taskId}`);
  return handleResponse(response);
};

export const fetchSonarResults = async (projectKey, branch = 'main') => {
  const url = new URL(`${API_BASE_URL}/sonarcloud/results/${projectKey}`);
  url.searchParams.append('branch', branch);

  const response = await fetch(url);
  return handleResponse(response);
};

export const fetchQualityGate = async (projectKey, branch = 'main') => {
  const url = new URL(`${API_BASE_URL}/sonarcloud/quality-gate/${projectKey}`);
  url.searchParams.append('branch', branch);

  const response = await fetch(url);
  return handleResponse(response);
};
