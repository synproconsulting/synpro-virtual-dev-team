const GITHUB_API_BASE = 'https://api.github.com';

const getAuthHeaders = () => {
  const token = process.env.REACT_APP_GITHUB_TOKEN;
  const headers = {
    'Accept': 'application/vnd.github.v3+json',
    'Content-Type': 'application/json'
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
};

export const fetchGitHubWorkflows = async (repository) => {
  if (!repository) {
    throw new Error('Repository name is required (format: owner/repo)');
  }

  const [owner, repo] = repository.split('/');
  if (!owner || !repo) {
    throw new Error('Invalid repository format. Use: owner/repo');
  }

  try {
    const response = await fetch(
      `${GITHUB_API_BASE}/repos/${owner}/${repo}/actions/runs?per_page=12`,
      {
        headers: getAuthHeaders()
      }
    );

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Authentication failed. Check your GitHub token.');
      }
      if (response.status === 404) {
        throw new Error('Repository not found or no access.');
      }
      throw new Error(`GitHub API error: ${response.status}`);
    }

    const data = await response.json();
    return data.workflow_runs || [];
  } catch (error) {
    if (error.message.includes('fetch')) {
      throw new Error('Network error. Check your connection.');
    }
    throw error;
  }
};

export const fetchWorkflowDetails = async (repository, runId) => {
  if (!repository || !runId) {
    throw new Error('Repository and run ID are required');
  }

  const [owner, repo] = repository.split('/');
  
  try {
    const response = await fetch(
      `${GITHUB_API_BASE}/repos/${owner}/${repo}/actions/runs/${runId}`,
      {
        headers: getAuthHeaders()
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch workflow details: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    throw new Error(`Error fetching workflow details: ${error.message}`);
  }
};

export const fetchWorkflowJobs = async (repository, runId) => {
  if (!repository || !runId) {
    throw new Error('Repository and run ID are required');
  }

  const [owner, repo] = repository.split('/');
  
  try {
    const response = await fetch(
      `${GITHUB_API_BASE}/repos/${owner}/${repo}/actions/runs/${runId}/jobs`,
      {
        headers: getAuthHeaders()
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch workflow jobs: ${response.status}`);
    }

    const data = await response.json();
    return data.jobs || [];
  } catch (error) {
    throw new Error(`Error fetching workflow jobs: ${error.message}`);
  }
};

export const retriggerWorkflow = async (repository, runId) => {
  if (!repository || !runId) {
    throw new Error('Repository and run ID are required');
  }

  const [owner, repo] = repository.split('/');
  
  try {
    const response = await fetch(
      `${GITHUB_API_BASE}/repos/${owner}/${repo}/actions/runs/${runId}/rerun`,
      {
        method: 'POST',
        headers: getAuthHeaders()
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to retrigger workflow: ${response.status}`);
    }

    return { success: true };
  } catch (error) {
    throw new Error(`Error retriggering workflow: ${error.message}`);
  }
};