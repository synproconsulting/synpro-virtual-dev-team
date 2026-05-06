/**
 * Overview Dashboard API Helper
 * Additional API functions specifically for the Overview dashboard
 */

const GITHUB_API = "https://api.github.com";
const GH_REPO = import.meta.env.VITE_GITHUB_REPO || "synproconsulting/synpro-virtual-dev-team";
const GH_TOKEN = import.meta.env.VITE_GITHUB_TOKEN || "";
const API_URL = import.meta.env.VITE_API_URL || "";

const ghHeaders = () => ({
  Accept: "application/vnd.github+json",
  "Content-Type": "application/json",
  ...(GH_TOKEN ? { Authorization: `Bearer ${GH_TOKEN}` } : {}),
});

/**
 * Fetch comprehensive dashboard metrics
 * Aggregates data from GitHub and Jira
 */
export const fetchDashboardMetrics = async () => {
  try {
    const [commits, prs, runs, branches, jiraIssues] = await Promise.all([
      fetchRecentCommits(),
      fetchOpenPRs(),
      fetchWorkflowRuns(),
      fetchBranches(),
      fetchJiraIssues(),
    ]);

    // Calculate metrics
    const totalCommits = commits.length;
    const openPRs = prs.length;
    const totalRuns = runs.length;
    const successfulRuns = runs.filter((r) => r.conclusion === "success").length;
    const failedRuns = runs.filter((r) => r.conclusion === "failure").length;
    const ciSuccessRate = totalRuns > 0 ? Math.round((successfulRuns / totalRuns) * 100) : 0;

    const totalIssues = jiraIssues.length;
    const doneIssues = jiraIssues.filter((i) => i.status === "Done").length;
    const inProgressIssues = jiraIssues.filter((i) => i.status === "In Progress").length;
    const todoIssues = jiraIssues.filter((i) => i.status === "To Do").length;
    const totalPoints = jiraIssues.reduce((sum, i) => sum + (i.points || 0), 0);
    const donePoints = jiraIssues.filter((i) => i.status === "Done").reduce((sum, i) => sum + (i.points || 0), 0);

    // Calculate velocity (completed in last 7 days)
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    const recentCompletedIssues = jiraIssues.filter(
      (i) => i.status === "Done" && i.updated && new Date(i.updated) > weekAgo
    );
    const velocity = recentCompletedIssues.length;

    return {
      commits: {
        total: totalCommits,
        today: commits.filter((c) => isToday(c.commit.author.date)).length,
      },
      pullRequests: {
        open: openPRs,
        total: prs.length,
      },
      cicd: {
        totalRuns,
        successfulRuns,
        failedRuns,
        successRate: ciSuccessRate,
      },
      branches: {
        total: branches.length,
        active: branches.filter((b) => !b.name.includes("main") && !b.name.includes("master")).length,
      },
      jira: {
        totalIssues,
        doneIssues,
        inProgressIssues,
        todoIssues,
        totalPoints,
        donePoints,
        velocity,
        completionRate: totalIssues > 0 ? Math.round((doneIssues / totalIssues) * 100) : 0,
      },
    };
  } catch (error) {
    console.error("Error fetching dashboard metrics:", error);
    return {
      commits: { total: 0, today: 0 },
      pullRequests: { open: 0, total: 0 },
      cicd: { totalRuns: 0, successfulRuns: 0, failedRuns: 0, successRate: 0 },
      branches: { total: 0, active: 0 },
      jira: {
        totalIssues: 0,
        doneIssues: 0,
        inProgressIssues: 0,
        todoIssues: 0,
        totalPoints: 0,
        donePoints: 0,
        velocity: 0,
        completionRate: 0,
      },
    };
  }
};

/**
 * Fetch recent commits (last 30 days)
 */
export const fetchRecentCommits = async () => {
  try {
    const since = new Date();
    since.setDate(since.getDate() - 30);
    const r = await fetch(
      `${GITHUB_API}/repos/${GH_REPO}/commits?since=${since.toISOString()}&per_page=100`,
      { headers: ghHeaders() }
    );
    return r.ok ? await r.json() : [];
  } catch (error) {
    console.error("Error fetching commits:", error);
    return [];
  }
};

/**
 * Fetch open pull requests
 */
export const fetchOpenPRs = async () => {
  try {
    const r = await fetch(`${GITHUB_API}/repos/${GH_REPO}/pulls?state=open&per_page=50`, {
      headers: ghHeaders(),
    });
    return r.ok ? await r.json() : [];
  } catch (error) {
    console.error("Error fetching PRs:", error);
    return [];
  }
};

/**
 * Fetch workflow runs
 */
export const fetchWorkflowRuns = async (perPage = 20) => {
  try {
    const r = await fetch(`${GITHUB_API}/repos/${GH_REPO}/actions/runs?per_page=${perPage}`, {
      headers: ghHeaders(),
    });
    return r.ok ? (await r.json()).workflow_runs || [] : [];
  } catch (error) {
    console.error("Error fetching workflow runs:", error);
    return [];
  }
};

/**
 * Fetch repository branches
 */
export const fetchBranches = async () => {
  try {
    const r = await fetch(`${GITHUB_API}/repos/${GH_REPO}/branches?per_page=100`, {
      headers: ghHeaders(),
    });
    return r.ok ? await r.json() : [];
  } catch (error) {
    console.error("Error fetching branches:", error);
    return [];
  }
};

/**
 * Fetch Jira issues via backend proxy
 */
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
  } catch (error) {
    console.error("Jira proxy error:", error);
    return [];
  }
};

/**
 * Fetch team activity (contributors, commits, etc.)
 */
export const fetchTeamActivity = async () => {
  try {
    const [contributors, stats] = await Promise.all([fetchContributors(), fetchRepoStats()]);

    return {
      contributors: contributors.slice(0, 10),
      totalContributors: contributors.length,
      stats,
    };
  } catch (error) {
    console.error("Error fetching team activity:", error);
    return {
      contributors: [],
      totalContributors: 0,
      stats: null,
    };
  }
};

/**
 * Fetch repository contributors
 */
export const fetchContributors = async () => {
  try {
    const r = await fetch(`${GITHUB_API}/repos/${GH_REPO}/contributors?per_page=50`, {
      headers: ghHeaders(),
    });
    return r.ok ? await r.json() : [];
  } catch (error) {
    console.error("Error fetching contributors:", error);
    return [];
  }
};

/**
 * Fetch repository statistics
 */
export const fetchRepoStats = async () => {
  try {
    const r = await fetch(`${GITHUB_API}/repos/${GH_REPO}`, { headers: ghHeaders() });
    if (!r.ok) return null;
    const data = await r.json();
    return {
      stars: data.stargazers_count || 0,
      forks: data.forks_count || 0,
      openIssues: data.open_issues_count || 0,
      size: data.size || 0,
      language: data.language || "Unknown",
      createdAt: data.created_at,
      updatedAt: data.updated_at,
    };
  } catch (error) {
    console.error("Error fetching repo stats:", error);
    return null;
  }
};

/**
 * Fetch code frequency (additions/deletions over time)
 */
export const fetchCodeFrequency = async () => {
  try {
    const r = await fetch(`${GITHUB_API}/repos/${GH_REPO}/stats/code_frequency`, {
      headers: ghHeaders(),
    });
    return r.ok ? await r.json() : [];
  } catch (error) {
    console.error("Error fetching code frequency:", error);
    return [];
  }
};

/**
 * Fetch deployment status
 */
export const fetchDeployments = async () => {
  try {
    const r = await fetch(`${GITHUB_API}/repos/${GH_REPO}/deployments?per_page=10`, {
      headers: ghHeaders(),
    });
    return r.ok ? await r.json() : [];
  } catch (error) {
    console.error("Error fetching deployments:", error);
    return [];
  }
};

/**
 * Helper function to check if a date is today
 */
function isToday(dateString) {
  if (!dateString) return false;
  const date = new Date(dateString);
  const today = new Date();
  return (
    date.getDate() === today.getDate() &&
    date.getMonth() === today.getMonth() &&
    date.getFullYear() === today.getFullYear()
  );
}

/**
 * Format time ago helper
 */
export const formatTimeAgo = (dateString) => {
  if (!dateString) return "Unknown";
  const now = new Date();
  const past = new Date(dateString);
  const diffMs = now - past;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins} min ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
  return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
};

/**
 * Calculate trend percentage
 */
export const calculateTrend = (current, previous) => {
  if (previous === 0) return current > 0 ? 100 : 0;
  return Math.round(((current - previous) / previous) * 100);
};
