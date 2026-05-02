/**
 * Dashboard API - Provides system status and metrics for the Overview tab
 */

const API_URL = import.meta.env.VITE_API_URL || "";
const GITHUB_API = "https://api.github.com";
const GH_REPO = import.meta.env.VITE_GITHUB_REPO || "synproconsulting/synpro-virtual-dev-team";
const GH_TOKEN = import.meta.env.VITE_GITHUB_TOKEN || "";

const ghHeaders = () => ({
  "Accept": "application/vnd.github+json",
  "Content-Type": "application/json",
  ...(GH_TOKEN ? { "Authorization": `Bearer ${GH_TOKEN}` } : {}),
});

/**
 * Fetch system status for all integrated services
 */
export const fetchSystemStatus = async () => {
  const status = {
    overall: "operational",
    services: {
      github: "operational",
      jira: "operational",
      uat: "operational"
    },
    lastChecked: new Date().toISOString()
  };

  try {
    // Check GitHub
    const ghResponse = await fetch(`${GITHUB_API}/repos/${GH_REPO}`, {
      headers: ghHeaders()
    });
    status.services.github = ghResponse.ok ? "operational" : "degraded";

    // Check Jira (through backend proxy)
    if (API_URL) {
      const jiraResponse = await fetch(`${API_URL}/proxy/jira/issues?maxResults=1`);
      status.services.jira = jiraResponse.ok ? "operational" : "degraded";
    }

    // Check UAT (through backend health endpoint)
    if (API_URL) {
      const uatResponse = await fetch(`${API_URL}/health`);
      status.services.uat = uatResponse.ok ? "operational" : "degraded";
    }

    // Determine overall status
    const servicesArray = Object.values(status.services);
    if (servicesArray.some(s => s === "down")) {
      status.overall = "degraded";
    } else if (servicesArray.some(s => s === "degraded")) {
      status.overall = "degraded";
    }

  } catch (error) {
    console.error("Error checking system status:", error);
    status.overall = "degraded";
  }

  return status;
};

/**
 * Fetch dashboard metrics (sprints, PRs, workflows, deployments)
 */
export const fetchDashboardMetrics = async () => {
  const metrics = {
    activeSprints: 0,
    openPRs: 0,
    activeWorkflows: 0,
    todayDeploys: 0,
    recentActivity: []
  };

  try {
    // Fetch active sprints
    if (API_URL) {
      const sprintsResponse = await fetch(`${API_URL}/proxy/jira/sprints`);
      if (sprintsResponse.ok) {
        const sprintsData = await sprintsResponse.json();
        const sprints = sprintsData.sprints || [];
        metrics.activeSprints = sprints.filter(s => s.state === "active").length;
      }
    }

    // Fetch open PRs
    const prsResponse = await fetch(
      `${GITHUB_API}/repos/${GH_REPO}/pulls?state=open&per_page=100`,
      { headers: ghHeaders() }
    );
    if (prsResponse.ok) {
      const prs = await prsResponse.json();
      metrics.openPRs = prs.length;
    }

    // Fetch recent workflow runs
    const runsResponse = await fetch(
      `${GITHUB_API}/repos/${GH_REPO}/actions/runs?per_page=20`,
      { headers: ghHeaders() }
    );
    if (runsResponse.ok) {
      const runsData = await runsResponse.json();
      const runs = runsData.workflow_runs || [];
      metrics.activeWorkflows = runs.filter(
        r => r.status === "in_progress" || r.status === "queued"
      ).length;

      // Count deployments today (workflow runs with "deploy" in name)
      const today = new Date().toDateString();
      metrics.todayDeploys = runs.filter(r => {
        const runDate = new Date(r.created_at).toDateString();
        const isDeployWorkflow = r.name?.toLowerCase().includes("deploy") || 
                                r.name?.toLowerCase().includes("uat");
        return runDate === today && isDeployWorkflow && r.conclusion === "success";
      }).length;

      // Get recent activity
      metrics.recentActivity = runs.slice(0, 5).map(r => ({
        type: "workflow",
        name: r.name,
        status: r.status,
        conclusion: r.conclusion,
        timestamp: r.created_at,
        url: r.html_url
      }));
    }

  } catch (error) {
    console.error("Error fetching dashboard metrics:", error);
  }

  return metrics;
};

/**
 * Fetch quick stats for the overview
 */
export const fetchOverviewStats = async () => {
  try {
    const [status, metrics] = await Promise.all([
      fetchSystemStatus(),
      fetchDashboardMetrics()
    ]);

    return {
      status,
      metrics,
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    console.error("Error fetching overview stats:", error);
    return {
      status: {
        overall: "unknown",
        services: {
          github: "unknown",
          jira: "unknown",
          uat: "unknown"
        }
      },
      metrics: {
        activeSprints: 0,
        openPRs: 0,
        activeWorkflows: 0,
        todayDeploys: 0
      },
      timestamp: new Date().toISOString()
    };
  }
};

/**
 * Fetch recent activity feed
 */
export const fetchRecentActivity = async (limit = 10) => {
  const activities = [];

  try {
    // Get recent workflow runs
    const runsResponse = await fetch(
      `${GITHUB_API}/repos/${GH_REPO}/actions/runs?per_page=${limit}`,
      { headers: ghHeaders() }
    );
    if (runsResponse.ok) {
      const runsData = await runsResponse.json();
      const runs = runsData.workflow_runs || [];
      activities.push(...runs.map(r => ({
        type: "workflow",
        id: r.id,
        name: r.name,
        status: r.status,
        conclusion: r.conclusion,
        timestamp: r.created_at,
        url: r.html_url,
        actor: r.actor?.login
      })));
    }

    // Get recent PRs
    const prsResponse = await fetch(
      `${GITHUB_API}/repos/${GH_REPO}/pulls?state=all&per_page=${limit}&sort=updated&direction=desc`,
      { headers: ghHeaders() }
    );
    if (prsResponse.ok) {
      const prs = await prsResponse.json();
      activities.push(...prs.map(pr => ({
        type: "pull_request",
        id: pr.number,
        name: pr.title,
        status: pr.state,
        merged: pr.merged_at ? "merged" : null,
        timestamp: pr.updated_at,
        url: pr.html_url,
        actor: pr.user?.login
      })));
    }

    // Sort by timestamp
    activities.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

    return activities.slice(0, limit);
  } catch (error) {
    console.error("Error fetching recent activity:", error);
    return [];
  }
};
