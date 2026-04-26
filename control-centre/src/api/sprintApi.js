const GITHUB_API = "https://api.github.com";
const GH_REPO   = import.meta.env.VITE_GITHUB_REPO || "synproconsulting/synpro-virtual-dev-team";
const GH_TOKEN  = import.meta.env.VITE_GITHUB_TOKEN || "";

const ghHeaders = () => ({
  "Accept": "application/vnd.github+json",
  "Content-Type": "application/json",
  ...(GH_TOKEN ? { "Authorization": `Bearer ${GH_TOKEN}` } : {}),
});

export const fetchSprintData = async () => {
  try {
    const [prsRes, runsRes] = await Promise.all([
      fetch(`${GITHUB_API}/repos/${GH_REPO}/pulls?state=open&per_page=20`, { headers: ghHeaders() }),
      fetch(`${GITHUB_API}/repos/${GH_REPO}/actions/runs?per_page=10`, { headers: ghHeaders() }),
    ]);
    const prs  = prsRes.ok  ? await prsRes.json() : [];
    const runs = runsRes.ok ? (await runsRes.json()).workflow_runs || [] : [];
    return { prs, runs, tickets: [] };
  } catch (e) {
    return { prs: [], runs: [], tickets: [] };
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
          body: JSON.stringify({ ref: "main", inputs: { ticket: ticket.key || ticket, summary: ticket.summary || ticket, feedback: "" } }) }
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
