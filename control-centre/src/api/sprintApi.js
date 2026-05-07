const GITHUB_API = "https://api.github.com";
const GH_REPO    = import.meta.env.VITE_GITHUB_REPO || "synproconsulting/synpro-virtual-dev-team";
const GH_TOKEN   = import.meta.env.VITE_GITHUB_TOKEN || "";
const API_URL    = import.meta.env.VITE_API_URL || "";

const ghHeaders = () => ({
  "Accept": "application/vnd.github+json",
  "Content-Type": "application/json",
  ...(GH_TOKEN ? { "Authorization": `Bearer ${GH_TOKEN}` } : {}),
});

// Jira calls go through the backend proxy to avoid CORS
export const fetchJiraIssues = async (status = null) => {
  if (!API_URL) return [];
  try {
    const url = status
      ? `${API_URL}/proxy/jira/issues?status=${encodeURIComponent(status)}`
      : `${API_URL}/proxy/jira/issues`;
    const r = await fetch(url);
    if (!r.ok) return [];
    const data = await r.json();
    return data.issues || [];
  } catch (e) {
    console.error("Jira proxy error:", e);
    return [];
  }
};

export const fetchSprintData = async () => {
  try {
    const [prsRes, runsRes, jiraIssues] = await Promise.all([
      fetch(`${GITHUB_API}/repos/${GH_REPO}/pulls?state=open&per_page=20`, { headers: ghHeaders() }),
      fetch(`${GITHUB_API}/repos/${GH_REPO}/actions/runs?per_page=10`, { headers: ghHeaders() }),
      fetchJiraIssues(),
    ]);
    const prs  = prsRes.ok  ? await prsRes.json() : [];
    const runs = runsRes.ok ? (await runsRes.json()).workflow_runs || [] : [];

    const doneIssues   = jiraIssues.filter(i => i.status === "Done");
    const totalPoints  = jiraIssues.reduce((s, i) => s + (i.points || 0), 0);
    const donePoints   = doneIssues.reduce((s, i) => s + (i.points || 0), 0);
    const successRuns  = runs.filter(r => r.conclusion === "success").length;

    return {
      prs,
      runs,
      jiraIssues,
      metrics: {
        velocity:      doneIssues.length,
        totalPoints,
        donePoints,
        openPRs:       prs.length,
        ciSuccessRate: runs.length ? Math.round((successRuns / runs.length) * 100) : 0,
      }
    };
  } catch (e) {
    return { prs: [], runs: [], jiraIssues: [], metrics: {} };
  }
};

export const triggerSprint = async (tickets = []) => {
  const [owner, repo] = GH_REPO.split("/");
  const results = [];
  for (const ticket of tickets) {
    try {
      const r = await fetch(
        `${GITHUB_API}/repos/${owner}/${repo}/actions/workflows/auto-implement.yml/dispatches`,
        { method: "POST", headers: ghHeaders(),
          body: JSON.stringify({ ref: "main", inputs: {
            ticket: ticket.key || ticket,
            summary: ticket.summary || ticket,
            feedback: ""
          }}) }
      );
      results.push({ ticket: ticket.key || ticket, status: r.status === 204 ? "triggered" : "failed" });
    } catch (e) {
      results.push({ ticket: ticket.key || ticket, status: "error" });
    }
  }
  return results;
};

export const triggerSprintRun = triggerSprint;

export const triggerAutoReview = async (prNumber) => {
  const [owner, repo] = GH_REPO.split("/");
  const r = await fetch(
    `${GITHUB_API}/repos/${owner}/${repo}/actions/workflows/auto-review.yml/dispatches`,
    { method: "POST", headers: ghHeaders(),
      body: JSON.stringify({ ref: "main", inputs: { pr_number: String(prNumber) } }) }
  );
  return { success: r.status === 204 };
};

export const fetchOpenPRs = async () => {
  const r = await fetch(`${GITHUB_API}/repos/${GH_REPO}/pulls?state=open&per_page=20`, { headers: ghHeaders() });
  return r.ok ? r.json() : [];
};

export const fetchWorkflowRuns = async (perPage = 10) => {
  const r = await fetch(`${GITHUB_API}/repos/${GH_REPO}/actions/runs?per_page=${perPage}`, { headers: ghHeaders() });
  return r.ok ? (await r.json()).workflow_runs || [] : [];
};

export const getSprintStatus = fetchSprintData;
export const getOpenPRs = fetchOpenPRs;

export const fetchSprints = async () => {
  const API_URL = import.meta.env.VITE_API_URL || "";
  if (!API_URL) return [];
  try {
    const r = await fetch(`${API_URL}/proxy/jira/sprints`);
    if (!r.ok) return [];
    const data = await r.json();
    return data.sprints || [];
  } catch (e) {
    console.error("Sprint fetch error:", e);
    return [];
  }
};

export const fetchSprintIssues = async (sprint) => {
  const API_URL = import.meta.env.VITE_API_URL || "";
  if (!API_URL || !sprint) return [];
  try {
    const sprintId = typeof sprint === "object" ? sprint.id : sprint;
    const nativeId = typeof sprint === "object" ? sprint.nativeId : null;
    const id = nativeId ? `${sprintId}|${nativeId}` : sprintId;
    const r = await fetch(`${API_URL}/proxy/jira/sprint/${id}/issues`);
    if (!r.ok) return [];
    const data = await r.json();
    return data.issues || [];
  } catch (e) {
    console.error("Sprint issues fetch error:", e);
    return [];
  }
};

export const fetchMergedPRs = async () => {
  try {
    // Fetch up to 100 closed PRs
    const r = await fetch(
      `${GITHUB_API}/repos/${GH_REPO}/pulls?state=closed&per_page=100&sort=updated&direction=desc`,
      { headers: ghHeaders() }
    );
    if (!r.ok) return [];
    const prs = await r.json();
    return prs
      .filter(pr => pr.merged_at) // only actually merged PRs
      .map(pr => {
        // Try matching [SDT1-26] pattern in title
        const titleMatch = pr.title.match(/\[([A-Z][A-Z0-9]+-\d+)\]/i);
        // Try matching feature/sdt1-26-... in branch name
        const branchMatch = pr.head?.ref?.match(/feature\/([a-zA-Z]+-\d+)[\-_]/i);
        const ticketKey = titleMatch
          ? titleMatch[1].toUpperCase()
          : branchMatch
            ? branchMatch[1].toUpperCase()
            : null;
        return {
          number:   pr.number,
          title:    pr.title,
          url:      pr.html_url,
          mergedAt: pr.merged_at,
          ticketKey,
        };
      })
      .filter(pr => pr.ticketKey);
  } catch (e) {
    console.error("fetchMergedPRs error:", e);
    return [];
  }
};

export const completeSprint = async (nativeSprintId, moveIncompleteTo = "backlog", nextSprintId = null) => {
  const API_URL = import.meta.env.VITE_API_URL || "";
  if (!API_URL) return { success: false, error: "API_URL not configured" };
  try {
    const body = { moveIncompleteTo };
    if (nextSprintId) body.nextSprintId = nextSprintId;
    const r = await fetch(`${API_URL}/proxy/jira/sprint/${nativeSprintId}/complete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      return { success: false, error: err.detail || `HTTP ${r.status}` };
    }
    return await r.json();
  } catch (e) {
    return { success: false, error: e.message };
  }
};
