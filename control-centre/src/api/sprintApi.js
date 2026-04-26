const GITHUB_API = "https://api.github.com";
const GH_REPO   = import.meta.env.VITE_GITHUB_REPO || "synproconsulting/synpro-virtual-dev-team";
const GH_TOKEN  = import.meta.env.VITE_GITHUB_TOKEN || "";
const JIRA_URL  = import.meta.env.VITE_JIRA_URL || "";
const JIRA_EMAIL = import.meta.env.VITE_JIRA_EMAIL || "";
const JIRA_TOKEN = import.meta.env.VITE_JIRA_API_TOKEN || "";
const JIRA_PROJECT = import.meta.env.VITE_JIRA_PROJECT_KEY || "SDT1";

const ghHeaders = () => ({
  "Accept": "application/vnd.github+json",
  "Content-Type": "application/json",
  ...(GH_TOKEN ? { "Authorization": `Bearer ${GH_TOKEN}` } : {}),
});

const jiraHeaders = () => ({
  "Accept": "application/json",
  "Content-Type": "application/json",
  ...(JIRA_EMAIL && JIRA_TOKEN
    ? { "Authorization": `Basic ${btoa(`${JIRA_EMAIL}:${JIRA_TOKEN}`)}` }
    : {}),
});

export const fetchJiraIssues = async (statusFilter = null) => {
  if (!JIRA_URL) return [];
  try {
    let jql = `project = ${JIRA_PROJECT} ORDER BY updated DESC`;
    if (statusFilter) {
      jql = `project = ${JIRA_PROJECT} AND status = "${statusFilter}" ORDER BY updated DESC`;
    }
    const r = await fetch(
      `${JIRA_URL}/rest/api/3/search/jql?jql=${encodeURIComponent(jql)}&maxResults=50&fields=summary,status,priority,issuetype,assignee,customfield_10016,customfield_10071`,
      { headers: jiraHeaders() }
    );
    if (!r.ok) return [];
    const data = await r.json();
    return (data.issues || []).map(i => ({
      key:     i.key,
      summary: i.fields.summary,
      status:  i.fields.status?.name || "Unknown",
      priority: i.fields.priority?.name || "Medium",
      type:    i.fields.issuetype?.name || "Story",
      points:  i.fields.customfield_10016 || 0,
      order:   i.fields.customfield_10071 || 999,
    }));
  } catch (e) {
    console.error("Jira fetch error:", e);
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

    // Compute metrics
    const doneIssues = jiraIssues.filter(i => i.status === "Done");
    const totalPoints = jiraIssues.reduce((s, i) => s + (i.points || 0), 0);
    const donePoints  = doneIssues.reduce((s, i) => s + (i.points || 0), 0);
    const successRuns = runs.filter(r => r.conclusion === "success").length;

    return {
      prs,
      runs,
      jiraIssues,
      metrics: {
        velocity:    doneIssues.length,
        totalPoints,
        donePoints,
        openPRs:     prs.length,
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
