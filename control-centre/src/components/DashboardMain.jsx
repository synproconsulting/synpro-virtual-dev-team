import React, { useState, useEffect } from "react";
import { fetchSprintData, fetchSprints, fetchWorkflowRuns } from "../api/sprintApi";
import { useProduct } from "../contexts/ProductContext";
import { Clock, GitPullRequest, CheckCircle2, AlertCircle, TrendingUp, Activity, Play, MessageSquare, Sparkles } from "lucide-react";

const StatCard = ({ icon: Icon, label, value, trend, color = "var(--accent)", loading = false }) => (
  <div style={{
    background: "var(--bg-card)",
    border: "1px solid var(--border)",
    borderRadius: 12,
    padding: "1.25rem",
    position: "relative",
    overflow: "hidden",
  }}>
    <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 12 }}>
      <div style={{
        width: 40,
        height: 40,
        borderRadius: 10,
        background: `${color}20`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: color,
      }}>
        <Icon size={20} />
      </div>
      {trend !== undefined && (
        <div style={{
          fontSize: 11,
          color: trend >= 0 ? "var(--success)" : "var(--danger)",
          display: "flex",
          alignItems: "center",
          gap: 2,
          fontWeight: 500,
        }}>
          <TrendingUp size={12} style={{ transform: trend >= 0 ? "none" : "rotate(180deg)" }} />
          {Math.abs(trend)}%
        </div>
      )}
    </div>
    <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: 6, fontWeight: 500 }}>{label}</div>
    <div style={{ fontSize: 28, fontWeight: 700, color: "var(--text)" }}>
      {loading ? "..." : value}
    </div>
  </div>
);

const ActivityItem = ({ type, title, subtitle, time, status }) => {
  const getStatusColor = () => {
    if (status === "success") return "var(--success)";
    if (status === "failure") return "var(--danger)";
    if (status === "in_progress") return "var(--accent)";
    return "var(--muted)";
  };

  const getIcon = () => {
    if (type === "pr") return <GitPullRequest size={14} />;
    if (type === "ci") return <Activity size={14} />;
    if (type === "ticket") return <CheckCircle2 size={14} />;
    return <Clock size={14} />;
  };

  return (
    <div style={{
      display: "flex",
      gap: 12,
      padding: "10px 0",
      borderBottom: "1px solid var(--border)",
    }}>
      <div style={{
        width: 32,
        height: 32,
        borderRadius: 8,
        background: `${getStatusColor()}20`,
        color: getStatusColor(),
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
      }}>
        {getIcon()}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: 13,
          fontWeight: 500,
          color: "var(--text)",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          marginBottom: 2,
        }}>
          {title}
        </div>
        <div style={{
          fontSize: 11,
          color: "var(--muted)",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}>
          {subtitle}
        </div>
      </div>
      <div style={{ fontSize: 11, color: "var(--muted)", flexShrink: 0 }}>
        {time}
      </div>
    </div>
  );
};

const QuickActionCard = ({ icon: Icon, label, description, onClick, color = "var(--accent)" }) => (
  <button
    onClick={onClick}
    style={{
      background: "var(--bg-card)",
      border: "1px solid var(--border)",
      borderRadius: 12,
      padding: "1.25rem",
      textAlign: "left",
      cursor: "pointer",
      transition: "all 0.2s",
      display: "flex",
      flexDirection: "column",
      gap: 10,
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.borderColor = color;
      e.currentTarget.style.transform = "translateY(-2px)";
      e.currentTarget.style.boxShadow = `0 4px 12px ${color}30`;
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.borderColor = "var(--border)";
      e.currentTarget.style.transform = "translateY(0)";
      e.currentTarget.style.boxShadow = "none";
    }}
  >
    <div style={{
      width: 40,
      height: 40,
      borderRadius: 10,
      background: `${color}20`,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: color,
    }}>
      <Icon size={20} />
    </div>
    <div>
      <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 12, color: "var(--muted)", lineHeight: 1.4 }}>
        {description}
      </div>
    </div>
  </button>
);

const HealthIndicator = ({ label, status, message }) => {
  const getColor = () => {
    if (status === "healthy") return "var(--success)";
    if (status === "warning") return "var(--warning)";
    return "var(--danger)";
  };

  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: 10,
      padding: "8px 0",
    }}>
      <div style={{
        width: 8,
        height: 8,
        borderRadius: "50%",
        background: getColor(),
        boxShadow: `0 0 8px ${getColor()}`,
      }} />
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 500, color: "var(--text)" }}>{label}</div>
        <div style={{ fontSize: 11, color: "var(--muted)" }}>{message}</div>
      </div>
    </div>
  );
};

const EmptyState = ({ message }) => (
  <div style={{
    textAlign: "center",
    color: "var(--muted)",
    padding: "3rem 1rem",
    background: "var(--bg-card)",
    border: "1px solid var(--border)",
    borderRadius: 12,
  }}>
    {message}
  </div>
);

const DashboardMain = () => {
  const { productCredentials, loadingCredentials, credentialsError } = useProduct();
  const productId = productCredentials?.id || null;

  const [data, setData] = useState(null);
  const [sprints, setSprints] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!productCredentials) {
      setData(null);
      setSprints([]);
      setLoading(false);
      return;
    }
    let cancelled = false;
    const loadData = async () => {
      setLoading(true);
      const [globalData, sprintList] = await Promise.all([
        fetchSprintData(productCredentials),
        fetchSprints(productId),
      ]);
      if (cancelled) return;
      setData(globalData);
      setSprints(sprintList);
      setLoading(false);
    };
    loadData();
    const interval = setInterval(loadData, 60000);
    return () => { cancelled = true; clearInterval(interval); };
  }, [productCredentials, productId]);

  const navigateToTab = (tabId) => {
    const navButtons = document.querySelectorAll(".cc-nav-btn");
    navButtons.forEach(btn => {
      if (btn.textContent.toLowerCase().includes(tabId)) {
        btn.click();
      }
    });
  };

  if (loadingCredentials) {
    return <EmptyState message="Loading product credentials…" />;
  }
  if (credentialsError) {
    return <EmptyState message={`Error loading credentials: ${credentialsError}`} />;
  }
  if (!productCredentials) {
    return <EmptyState message="Select a product to view overview" />;
  }

  const metrics = data?.metrics || {};
  const prs = data?.prs || [];
  const runs = data?.runs || [];
  const issues = data?.jiraIssues || [];

  const recentActivity = [];

  prs.slice(0, 3).forEach(pr => {
    recentActivity.push({
      type: "pr",
      title: `PR #${pr.number}: ${pr.title}`,
      subtitle: `by ${pr.user?.login || "unknown"}`,
      time: getTimeAgo(pr.created_at),
      status: "in_progress",
    });
  });

  runs.slice(0, 2).forEach(run => {
    recentActivity.push({
      type: "ci",
      title: run.name || "Workflow",
      subtitle: run.head_commit?.message?.split("\n")[0] || "Running...",
      time: getTimeAgo(run.created_at),
      status: run.conclusion || "in_progress",
    });
  });

  issues.filter(i => i.status === "Done").slice(0, 2).forEach(issue => {
    recentActivity.push({
      type: "ticket",
      title: `${issue.key}: ${issue.summary}`,
      subtitle: `${issue.points || 0} points`,
      time: "Recently",
      status: "success",
    });
  });

  recentActivity.sort((a, b) => {
    const timeToMinutes = (t) => {
      if (t.includes("min")) return parseInt(t);
      if (t.includes("hour")) return parseInt(t) * 60;
      if (t.includes("day")) return parseInt(t) * 1440;
      return 0;
    };
    return timeToMinutes(a.time) - timeToMinutes(b.time);
  });

  const ciHealth = metrics.ciSuccessRate >= 80 ? "healthy" : metrics.ciSuccessRate >= 60 ? "warning" : "error";
  const prHealth = prs.length <= 10 ? "healthy" : prs.length <= 20 ? "warning" : "error";
  const sprintHealth = metrics.velocity > 0 ? "healthy" : "warning";

  const activeSprint = sprints.length > 0 ? sprints[sprints.length - 1] : null;
  const completionRate = issues.length > 0
    ? Math.round((issues.filter(i => i.status === "Done").length / issues.length) * 100)
    : 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>

      {/* Welcome Header */}
      <div style={{
        background: "linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(139,92,246,0.1) 100%)",
        border: "1px solid rgba(99,102,241,0.2)",
        borderRadius: 16,
        padding: "2rem",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
          <Sparkles size={28} color="var(--accent)" />
          <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0 }}>
            SynPro Control Centre
          </h1>
        </div>
        <p style={{ fontSize: 14, color: "var(--muted)", margin: 0, maxWidth: 600 }}>
          Welcome back! Here's your development workflow at a glance. Manage sprints,
          monitor deployments, and leverage AI-assisted planning all in one place.
        </p>
        {activeSprint && (
          <div style={{
            marginTop: 16,
            padding: "8px 12px",
            background: "rgba(99,102,241,0.15)",
            borderRadius: 8,
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            fontSize: 12,
          }}>
            <Activity size={14} color="var(--accent)" />
            <span style={{ fontWeight: 500 }}>Active Sprint:</span>
            <span style={{ color: "var(--accent)" }}>{activeSprint.name}</span>
            <span style={{ color: "var(--muted)" }}>· {completionRate}% complete</span>
          </div>
        )}
      </div>

      {/* Key Metrics */}
      <div>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: "var(--text)" }}>
          Key Metrics
        </h2>
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: 12,
        }}>
          <StatCard
            icon={CheckCircle2}
            label="Sprint Velocity"
            value={loading ? "..." : metrics.velocity || 0}
            trend={12}
            color="var(--success)"
            loading={loading}
          />
          <StatCard
            icon={TrendingUp}
            label="Story Points"
            value={loading ? "..." : `${metrics.donePoints || 0}/${metrics.totalPoints || 0}`}
            color="var(--accent)"
            loading={loading}
          />
          <StatCard
            icon={GitPullRequest}
            label="Open Pull Requests"
            value={loading ? "..." : prs.length}
            color="#8b5cf6"
            loading={loading}
          />
          <StatCard
            icon={Activity}
            label="CI Success Rate"
            value={loading ? "..." : `${metrics.ciSuccessRate || 0}%`}
            trend={5}
            color={metrics.ciSuccessRate >= 80 ? "var(--success)" : "var(--warning)"}
            loading={loading}
          />
        </div>
      </div>

      {/* Quick Actions & Recent Activity */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
        gap: "1.5rem",
      }}>

        {/* Quick Actions */}
        <div>
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: "var(--text)" }}>
            Quick Actions
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <QuickActionCard
              icon={Play}
              label="View Sprint Status"
              description="Monitor current sprint progress and manage tickets"
              onClick={() => navigateToTab("sprint")}
              color="var(--accent)"
            />
            <QuickActionCard
              icon={MessageSquare}
              label="Chat with PM Agent"
              description="Plan sprints and get AI-assisted project insights"
              onClick={() => navigateToTab("pm agent")}
              color="#8b5cf6"
            />
            <QuickActionCard
              icon={Activity}
              label="Monitor Workflows"
              description="Track GitHub Actions and CI/CD pipeline status"
              onClick={() => navigateToTab("workflows")}
              color="#22c55e"
            />
          </div>
        </div>

        {/* Recent Activity */}
        <div>
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: "var(--text)" }}>
            Recent Activity
          </h2>
          <div style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            padding: "1rem",
            minHeight: 300,
          }}>
            {loading ? (
              <div style={{ textAlign: "center", color: "var(--muted)", padding: "2rem" }}>
                Loading activity...
              </div>
            ) : recentActivity.length === 0 ? (
              <div style={{ textAlign: "center", color: "var(--muted)", padding: "2rem" }}>
                No recent activity
              </div>
            ) : (
              recentActivity.slice(0, 6).map((activity, idx) => (
                <ActivityItem key={idx} {...activity} />
              ))
            )}
          </div>
        </div>
      </div>

      {/* System Health */}
      <div>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: "var(--text)" }}>
          System Health
        </h2>
        <div style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          borderRadius: 12,
          padding: "1.25rem",
        }}>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "1rem",
          }}>
            <HealthIndicator
              label="CI/CD Pipeline"
              status={ciHealth}
              message={`${metrics.ciSuccessRate || 0}% success rate over last 10 runs`}
            />
            <HealthIndicator
              label="Pull Request Queue"
              status={prHealth}
              message={`${prs.length} open PRs awaiting review`}
            />
            <HealthIndicator
              label="Sprint Progress"
              status={sprintHealth}
              message={`${metrics.velocity || 0} tickets completed · ${completionRate}% done`}
            />
          </div>
        </div>
      </div>

      {/* Pro Tip */}
      <div style={{
        background: "rgba(99,102,241,0.08)",
        border: "1px solid rgba(99,102,241,0.2)",
        borderRadius: 12,
        padding: "1rem",
        fontSize: 13,
        display: "flex",
        alignItems: "flex-start",
        gap: 12,
      }}>
        <div style={{ fontSize: 20 }}>💡</div>
        <div>
          <strong style={{ color: "var(--text)" }}>Pro Tip:</strong>{" "}
          <span style={{ color: "var(--muted)" }}>
            Use the <strong style={{ color: "var(--accent)" }}>Sprint Status</strong> tab to
            run tickets with one click, or head to <strong style={{ color: "var(--accent)" }}>PM Agent</strong> to
            plan your next sprint using AI-powered insights.
          </span>
        </div>
      </div>

    </div>
  );
};

function getTimeAgo(dateString) {
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
}

export default DashboardMain;
