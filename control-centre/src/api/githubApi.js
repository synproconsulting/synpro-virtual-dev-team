const GITHUB_API = "https://api.github.com";
const GH_REPO   = import.meta.env.VITE_GITHUB_REPO || "synproconsulting/synpro-virtual-dev-team";
const GH_TOKEN  = import.meta.env.VITE_GITHUB_TOKEN || "";

const getAuthHeaders = () => ({
  "Accept": "application/vnd.github.v3+json",
  "Content-Type": "application/json",
  ...(GH_TOKEN ? { "Authorization": `Bearer ${GH_TOKEN}` } : {}),
});

// Derive ticketKey (Jira) and prNumber from a GitHub workflow run.
// ticketKey: tries head_branch first (e.g. feature/sdt1-90-foo), then display_title
//   (e.g. "feat(SDT1-90): ..." or "[SDT1-90] ..."). Returns null if neither matches.
// prNumber: pull_requests[0].number when GitHub populated it (open same-repo PR runs).
const annotateRun = (run) => {
  const branchMatch = run.head_branch?.match(/[a-zA-Z]+\/([a-zA-Z][a-zA-Z0-9]*-\d+)[-_]/i);
  const titleMatch  = run.display_title?.match(/(?:\(([A-Z][A-Z0-9]+-\d+)\)|\[([A-Z][A-Z0-9]+-\d+)\])/i);
  const ticketKey = branchMatch
    ? branchMatch[1].toUpperCase()
    : titleMatch
      ? (titleMatch[1] || titleMatch[2]).toUpperCase()
      : null;
  const prNumber = run.pull_requests?.[0]?.number ?? null;
  return { ...run, ticketKey, prNumber };
};

export const fetchGitHubWorkflows = async (repository) => {
  const repo = repository || GH_REPO;
  const r = await fetch(`${GITHUB_API}/repos/${repo}/actions/runs?per_page=12`, { headers: getAuthHeaders() });
  if (!r.ok) throw new Error(`GitHub API error: ${r.status}`);
  const runs = (await r.json()).workflow_runs || [];
  return runs.map(annotateRun);
};

export const fetchWorkflowDetails = async (repository, runId) => {
  const repo = repository || GH_REPO;
  const r = await fetch(`${GITHUB_API}/repos/${repo}/actions/runs/${runId}`, { headers: getAuthHeaders() });
  if (!r.ok) throw new Error(`Failed to fetch workflow details: ${r.status}`);
  return r.json();
};

export const fetchWorkflowJobs = async (repository, runId) => {
  const repo = repository || GH_REPO;
  const r = await fetch(`${GITHUB_API}/repos/${repo}/actions/runs/${runId}/jobs`, { headers: getAuthHeaders() });
  if (!r.ok) throw new Error(`Failed to fetch workflow jobs: ${r.status}`);
  return (await r.json()).jobs || [];
};

export const retriggerWorkflow = async (repository, runId) => {
  const repo = repository || GH_REPO;
  const r = await fetch(`${GITHUB_API}/repos/${repo}/actions/runs/${runId}/rerun`,
    { method: "POST", headers: getAuthHeaders() });
  return { success: r.ok };
};

export const fetchWorkflowRuns = async (perPage = 12) => {
  return fetchGitHubWorkflows(GH_REPO);
};

export const triggerWorkflow = async (workflowFile, inputs = {}) => {
  const [owner, repo] = GH_REPO.split("/");
  const r = await fetch(
    `${GITHUB_API}/repos/${owner}/${repo}/actions/workflows/${workflowFile}/dispatches`,
    { method: "POST", headers: getAuthHeaders(),
      body: JSON.stringify({ ref: "main", inputs }) }
  );
  return { success: r.status === 204 };
};
