const GITHUB_API = "https://api.github.com";
const GH_REPO    = import.meta.env.VITE_GITHUB_REPO || "synproconsulting/synpro-virtual-dev-team";
const GH_TOKEN   = import.meta.env.VITE_GITHUB_TOKEN || "";
const API_URL    = import.meta.env.VITE_API_URL || "";

const ghHeaders = () => ({
  "Accept": "application/vnd.github+json",
  "Content-Type": "application/json",
  ...(GH_TOKEN ? { "Authorization": `Bearer ${GH_TOKEN}` } : {}),
});

// Use product config for GitHub repo when a product is selected
const getGhRepo = (product) =>
  product?.github_org && product?.github_repo
    ? `${product.github_org}/${product.github_repo}`
    : GH_REPO;

// Jira calls go through the backend proxy to avoid CORS.
// Pass product_id when a product is selected so the proxy uses product-specific config.
export const fetchJiraIssues = async (status = null, productId = null) => {
  if (!API_URL) return [];
  try {
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (productId) params.set("product_id", productId);
    const qs = params.toString();
    const url = `${API_URL}/proxy/jira/issues${qs ? "?" + qs : ""}`;
    const r = await fetch(url);
    if (!r.ok) return [];
    const data = await r.json();
    return data.issues || [];
  } catch (e) {
    console.error("Jira proxy error:", e);
    return [];
  }
};

export const fetchSprintData = async (product = null) => {
  const repo = getGhRepo(product);
  try {
    const [prsRes, runsRes, jiraIssues] = await Promise.all([
      fetch(`${GITHUB_API}/repos/${repo}/pulls?state=open&per_page=20`, { headers: ghHeaders() }),
      fetch(`${GITHUB_API}/repos/${repo}/actions/runs?per_page=10`, { headers: ghHeaders() }),
      fetchJiraIssues(null, product?.id),
    ]);
    const rawPrs = prsRes.ok ? await prsRes.json() : [];
    const prs = rawPrs.map(pr => {
      const titleMatch  = pr.title?.match(/\[([A-Z][A-Z0-9]+-\d+)\]/i);
      const branchMatch = pr.head?.ref?.match(/feature\/([a-zA-Z]+-\d+)[\-_]/i);
      const ticketKey = titleMatch
        ? titleMatch[1].toUpperCase()
        : branchMatch
          ? branchMatch[1].toUpperCase()
          : null;
      return { ...pr, ticketKey };
    });
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

export const fetchOpenPRs = async (product = null) => {
  const repo = getGhRepo(product);
  const r = await fetch(`${GITHUB_API}/repos/${repo}/pulls?state=open&per_page=20`, { headers: ghHeaders() });
  return r.ok ? r.json() : [];
};

export const fetchWorkflowRuns = async (perPage = 10, product = null) => {
  const repo = getGhRepo(product);
  const r = await fetch(`${GITHUB_API}/repos/${repo}/actions/runs?per_page=${perPage}`, { headers: ghHeaders() });
  return r.ok ? (await r.json()).workflow_runs || [] : [];
};

export const getSprintStatus = fetchSprintData;
export const getOpenPRs = fetchOpenPRs;

export const fetchSprints = async (productId = null) => {
  const API_URL = import.meta.env.VITE_API_URL || "";
  if (!API_URL) return [];
  try {
    const params = productId ? `?product_id=${encodeURIComponent(productId)}` : "";
    const r = await fetch(`${API_URL}/proxy/jira/sprints${params}`);
    if (!r.ok) return [];
    const data = await r.json();
    return data.sprints || [];
  } catch (e) {
    console.error("Sprint fetch error:", e);
    return [];
  }
};

export const fetchSprintIssues = async (sprint, productId = null) => {
  const API_URL = import.meta.env.VITE_API_URL || "";
  if (!API_URL || !sprint) return [];
  try {
    const sprintId = typeof sprint === "object" ? sprint.id : sprint;
    const nativeId = typeof sprint === "object" ? sprint.nativeId : null;
    const id = nativeId ? `${sprintId}|${nativeId}` : sprintId;
    const params = productId ? `?product_id=${encodeURIComponent(productId)}` : "";
    const r = await fetch(`${API_URL}/proxy/jira/sprint/${id}/issues${params}`);
    if (!r.ok) return [];
    const data = await r.json();
    return data.issues || [];
  } catch (e) {
    console.error("Sprint issues fetch error:", e);
    return [];
  }
};

export const fetchMergedPRs = async (product = null) => {
  const repo = getGhRepo(product);
  try {
    const r = await fetch(
      `${GITHUB_API}/repos/${repo}/pulls?state=closed&per_page=100&sort=updated&direction=desc`,
      { headers: ghHeaders() }
    );
    if (!r.ok) return [];
    const prs = await r.json();
    return prs
      .filter(pr => pr.merged_at)
      .map(pr => {
        const titleMatch = pr.title.match(/\[([A-Z][A-Z0-9]+-\d+)\]/i);
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