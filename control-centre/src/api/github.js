const GITHUB_API_BASE = 'https://api.github.com';
const GITHUB_TOKEN = process.env.REACT_APP_GITHUB_TOKEN;

class GitHubAPIError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'GitHubAPIError';
    this.status = status;
  }
}

const fetchWithAuth = async (url, options = {}) => {
  const headers = {
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    ...options.headers
  };

  if (GITHUB_TOKEN) {
    headers['Authorization'] = `Bearer ${GITHUB_TOKEN}`;
  }

  const response = await fetch(url, {
    ...options,
    headers
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new GitHubAPIError(
      errorData.message || `GitHub API error: ${response.statusText}`,
      response.status
    );
  }

  return response.json();
};

export const fetchGitHubWorkflows = async (repository) => {
  const [owner, repo] = repository.split('/');
  if (!owner || !repo) {
    throw new Error('Invalid repository format. Expected: owner/repo');
  }

  const url = `${GITHUB_API_BASE}/repos/${owner}/${repo}/actions/workflows`;
  const data = await fetchWithAuth(url);
  return data.workflows || [];
};

export const fetchWorkflowRuns = async (repository, workflowId, perPage = 5) => {
  const [owner, repo] = repository.split('/');
  if (!owner || !repo) {
    throw new Error('Invalid repository format. Expected: owner/repo');
  }

  const url = `${GITHUB_API_BASE}/repos/${owner}/${repo}/actions/workflows/${workflowId}/runs?per_page=${perPage}`;
  const data = await fetchWithAuth(url);
  
  return (data.workflow_runs || []).map(run => ({
    id: run.id,
    name: run.name,
    head_branch: run.head_branch,
    head_commit: run.head_commit,
    status: mapWorkflowStatus(run.status, run.conclusion),
    conclusion: run.conclusion,
    created_at: run.created_at,
    updated_at: run.updated_at,
    html_url: run.html_url,
    run_number: run.run_number,
    actor: run.actor,
    event: run.event
  }));
};

export const fetchWorkflowRunDetails = async (repository, runId) => {
  const [owner, repo] = repository.split('/');
  if (!owner || !repo) {
    throw new Error('Invalid repository format. Expected: owner/repo');
  }

  const url = `${GITHUB_API_BASE}/repos/${owner}/${repo}/actions/runs/${runId}`;
  return fetchWithAuth(url);
};

export const fetchWorkflowRunJobs = async (repository, runId) => {
  const [owner, repo] = repository.split('/');
  if (!owner || !repo) {
    throw new Error('Invalid repository format. Expected: owner/repo');
  }

  const url = `${GITHUB_API_BASE}/repos/${owner}/${repo}/actions/runs/${runId}/jobs`;
  const data = await fetchWithAuth(url);
  return data.jobs || [];
};

const mapWorkflowStatus = (status, conclusion) => {
  if (status === 'completed') {
    switch (conclusion) {
      case 'success':
        return 'success';
      case 'failure':
        return 'failure';
      case 'cancelled':
        return 'cancelled';
      default:
        return 'failure';
    }
  }
  if (status === 'in_progress') {
    return 'in_progress';
  }
  if (status === 'queued' || status === 'waiting') {
    return 'queued';
  }
  return 'unknown';
};

export const getWorkflowSummary = async (repository) => {
  const workflows = await fetchGitHubWorkflows(repository);
  const summary = {
    total: workflows.length,
    active: 0,
    disabled: 0,
    recentRuns: []
  };

  for (const workflow of workflows) {
    if (workflow.state === 'active') {
      summary.active++;
    } else {
      summary.disabled++;
    }
  }

  if (workflows.length > 0) {
    const firstWorkflow = workflows[0];
    const runs = await fetchWorkflowRuns(repository, firstWorkflow.id, 10);
    summary.recentRuns = runs;
  }

  return summary;
};