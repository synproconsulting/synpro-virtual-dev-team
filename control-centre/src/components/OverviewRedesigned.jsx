import React, { useState, useEffect } from "react";
import { fetchSprintData, fetchSprints, fetchWorkflowRuns } from "../api/sprintApi";
import {
  Clock,
  GitPullRequest,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  Activity,
  Play,
  MessageSquare,
  Sparkles,
  Zap,
  GitBranch,
  Target,
  BarChart3,
  Calendar,
  Users,
  Rocket,
  Code,
  GitCommit,
} from "lucide-react";

/**
 * Metric Card Component
 * Displays a key metric with icon, value, and optional trend indicator
 */
const MetricCard = ({ icon: Icon, label, value, trend, color = "var(--accent)", loading = false, subtitle }) => (
  <div
    style={{
      background: "var(--bg-card)",
      border: "1px solid var(--border)",
      borderRadius: 12,
      padding: "1.5rem",
      position: "relative",
      overflow: "hidden",
      transition: "all 0.2s",
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.borderColor = color;
      e.currentTarget.style.transform = "translateY(-2px)";
      e.currentTarget.style.boxShadow = `0 8px 24px ${color}20`;
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.borderColor = "var(--border)";
      e.currentTarget.style.transform = "translateY(0)";
      e.currentTarget.style.boxShadow = "none";
    }}
  >
    <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 16 }}>
      <div
        style={{
          width: 48,
          height: 48,
          borderRadius: 12,
          background: `${color}15`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: color,
        }}
      >
        <Icon size={24} />
      </div>
      {trend !== undefined && (
        <div
          style={{
            fontSize: 12,
            color: trend >= 0 ? "var(--success)" : "var(--danger)",
            display: "flex",
            alignItems: "center",
            gap: 4,
            fontWeight: 600,
            background: trend >= 0 ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)",
            padding: "4px 8px",
            borderRadius: 6,
          }}
        >
          <TrendingUp size={14} style={{ transform: trend >= 0 ? "none" : "rotate(180deg)" }} />
          {Math.abs(trend)}%
        </div>
      )}
    </div>
    <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: 8, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.5px" }}>
      {label}
    </div>
    <div style={{ fontSize: 32, fontWeight: 700, color: "var(--text)", marginBottom: 4 }}>
      {loading ? "..." : value}
    </div>
    {subtitle && (
      <div style={{ fontSize: 12, color: "var(--muted)" }}>
        {subtitle}
      </div>
    )}
  </div>
);

/**
 * Activity Timeline Item Component
 */
const ActivityTimelineItem = ({ type, title, subtitle, time, status, icon: CustomIcon }) => {
  const getStatusColor = () => {
    if (status === "success") return "var(--success)";
    if (status === "failure") return "var(--danger)";
    if (status === "in_progress") return "var(--accent)";
    return "var(--muted)";
  };

  const getIcon = () => {
    if (CustomIcon) return <CustomIcon size={16} />;
    if (type === "pr") return <GitPullRequest size={16} />;
    if (type === "ci") return <Activity size={16} />;
    if (type === "ticket") return <CheckCircle2 size={16} />;
    if (type === "deploy") return <Rocket size={16} />;
    return <Clock size={16} />;
  };

  return (
    <div
      style={{
        display: "flex",
        gap: 14,
        padding: "14px 0",
        borderBottom: "1px solid var(--border)",
        position: "relative",
      }}
    >
      {/* Timeline line */}
      <div
        style={{
          position: "absolute",
          left: 19,
          top: 46,
          bottom: -10,
          width: 2,
          background: "var(--border)",
        }}
      />
      
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: 10,
          background: `${getStatusColor()}20`,
          color: getStatusColor(),
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          border: `2px solid ${getStatusColor()}`,
          position: "relative",
          zIndex: 1,
        }}
      >
        {getIcon()}
      </div>
      
      <div style={{ flex: 1, minWidth: 0, paddingTop: 2 }}>
        <div
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: "var(--text)",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            marginBottom: 4,
          }}
        >
          {title}
        </div>
        <div
          style={{
            fontSize: 12,
            color: "var(--muted)",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {subtitle}
        </div>
      </div>
      
      <div style={{ fontSize: 11, color: "var(--muted)", flexShrink: 0, paddingTop: 2 }}>
        {time}
      </div>
    </div>
  );
};

/**
 * Quick Action Button Component
 */
const QuickActionButton = ({ icon: Icon, label, description, onClick, color = "var(--accent)", disabled = false }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    style={{
      background: "var(--bg-card)",
      border: "1px solid var(--border)",
      borderRadius: 12,
      padding: "1.25rem",
      textAlign: "left",
      cursor: disabled ? "not-allowed" : "pointer",
      transition: "all 0.2s",
      display: "flex",
      alignItems: "center",
      gap: 14,
      opacity: disabled ? 0.5 : 1,
    }}
    onMouseEnter={(e) => {
      if (!disabled) {
        e.currentTarget.style.borderColor = color;
        e.currentTarget.style.transform = "translateY(-2px)";
        e.currentTarget.style.boxShadow = `0 4px 16px ${color}30`;
      }
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.borderColor = "var(--border)";
      e.currentTarget.style.transform = "translateY(0)";
      e.currentTarget.style.boxShadow = "none";
    }}
  >
    <div
      style={{
        width: 48,
        height: 48,
        borderRadius: 10,
        background: `${color}20`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: color,
        flexShrink: 0,
      }}
    >
      <Icon size={24} />
    </div>
    <div style={{ flex: 1 }}>
      <div style={{ fontSize: 15, fontWeight: 600, color: "var(--text)", marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 12, color: "var(--muted)", lineHeight: 1.5 }}>
        {description}
      </div>
    </div>
  </button>
);

/**
 * System Health Status Component
 */
const HealthStatus = ({ label, status, message, metric }) => {
  const getColor = () => {
    if (status === "healthy") return "var(--success)";
    if (status === "warning") return "var(--warning)";
    return "var(--danger)";
  };

  const getStatusLabel = () => {
    if (status === "healthy") return "Healthy";
    if (status === "warning") return "Warning";
    return "Critical";
  };

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "12px 0",
      }}
    >
      <div
        style={{
          width: 10,
          height: 10,
          borderRadius: "50%",
          background: getColor(),
          boxShadow: `0 0 12px ${getColor()}`,
          animation: "pulse 2s infinite",
          flexShrink: 0,
        }}
      />
      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 2 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)" }}>{label}</div>
          <div
            style={{
              fontSize: 10,
              fontWeight: 600,
              color: getColor(),
              background: `${getColor()}20`,
              padding: "2px 6px",
              borderRadius: 4,
              textTransform: "uppercase",
              letterSpacing: "0.3px",
            }}
          >
            {getStatusLabel()}
          </div>
        </div>
        <div style={{ fontSize: 12, color: "var(--muted)" }}>{message}</div>
      </div>
      {metric !== undefined && (
        <div style={{ fontSize: 20, fontWeight: 700, color: getColor(), flexShrink: 0 }}>
          {metric}
        </div>
      )}
    </div>
  );
};

/**
 * Sprint Progress Ring Component
 */
const ProgressRing = ({ percentage, size = 120, strokeWidth = 8, color = "var(--accent)" }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div style={{ position: "relative", width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="var(--border)"
          strokeWidth={strokeWidth}
          fill="none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.5s ease" }}
        />
      </svg>
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          textAlign: "center",
        }}
      >
        <div style={{ fontSize: 24, fontWeight: 700, color: "var(--text)" }}>{percentage}%</div>
        <div style={{ fontSize: 10, color: "var(--muted)", marginTop: 2 }}>Complete</div>
      </div>
    </div>
  );
};

/**
 * Main Overview Dashboard Component
 */
const OverviewRedesigned = () => {
  const [data, setData] = useState(null);
  const [sprints, setSprints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      const [globalData, sprintList] = await Promise.all([
        fetchSprintData(),
        fetchSprints(),
      ]);
      setData(globalData);
      setSprints(sprintList);
      setLoading(false);
      setLastUpdate(new Date());
    };
    loadData();
    const interval = setInterval(loadData, 45000); // Refresh every 45 seconds
    return () => clearInterval(interval);
  }, []);

  const navigateToTab = (tabId) => {
    const navButtons = document.querySelectorAll(".cc-nav-btn");
    navButtons.forEach((btn) => {
      if (btn.textContent.toLowerCase().includes(tabId)) {
        btn.click();
      }
    });
  };

  const metrics = data?.metrics || {};
  const prs = data?.prs || [];
  const runs = data?.runs || [];
  const issues = data?.jiraIssues || [];

  // Calculate sprint completion
  const activeSprint = sprints.length > 0 ? sprints[sprints.length - 1] : null;
  const completionRate = issues.length > 0 ? Math.round((issues.filter((i) => i.status === "Done").length / issues.length) * 100) : 0;

  // Calculate system health
  const ciHealth = metrics.ciSuccessRate >= 80 ? "healthy" : metrics.ciSuccessRate >= 60 ? "warning" : "error";
  const prHealth = prs.length <= 10 ? "healthy" : prs.length <= 20 ? "warning" : "error";
  const sprintHealth = metrics.velocity > 0 ? "healthy" : "warning";

  // Build recent activity feed
  const recentActivity = [];

  prs.slice(0, 3).forEach((pr) => {
    recentActivity.push({
      type: "pr",
      title: `PR #${pr.number}: ${pr.title}`,
      subtitle: `by ${pr.user?.login || "unknown"} • Ready for review`,
      time: getTimeAgo(pr.created_at),
      status: "in_progress",
    });
  });

  runs.slice(0, 3).forEach((run) => {
    recentActivity.push({
      type: "ci",
      title: run.name || "Workflow Run",
      subtitle: run.head_commit?.message?.split("\n")[0] || "Pipeline running...",
      time: getTimeAgo(run.created_at),
      status: run.conclusion || "in_progress",
    });
  });

  issues
    .filter((i) => i.status === "Done")
    .slice(0, 2)
    .forEach((issue) => {
      recentActivity.push({
        type: "ticket",
        title: `${issue.key}: ${issue.summary}`,
        subtitle: `Completed • ${issue.points || 0} story points`,
        time: "Recently",
        status: "success",
      });
    });

  // Sort by most recent
  recentActivity.sort((a, b) => {
    const timeToMinutes = (t) => {
      if (t.includes("min")) return parseInt(t);
      if (t.includes("hour")) return parseInt(t) * 60;
      if (t.includes("day")) return parseInt(t) * 1440;
      return 9999;
    };
    return timeToMinutes(a.time) - timeToMinutes(b.time);
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
      
      {/* Hero Section */}
      <div
        style={{
          background: "linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(139,92,246,0.15) 100%)",
          border: "1px solid rgba(99,102,241,0.3)",
          borderRadius: 16,
          padding: "2.5rem",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div style={{ position: "absolute", top: 20, right: 20, fontSize: 60, opacity: 0.1 }}>⚡</div>
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 14 }}>
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 14,
              background: "linear-gradient(135deg, var(--accent) 0%, #8b5cf6 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 8px 24px rgba(99,102,241,0.4)",
            }}
          >
            <Sparkles size={32} color="white" />
          </div>
          <div>
            <h1 style={{ fontSize: 32, fontWeight: 700, margin: 0, marginBottom: 4 }}>SynPro Control Centre</h1>
            <p style={{ fontSize: 14, color: "var(--muted)", margin: 0 }}>
              AI-Powered Development Workflow • Last updated {getTimeAgo(lastUpdate)}
            </p>
          </div>
        </div>
        <p style={{ fontSize: 15, color: "var(--text)", margin: 0, maxWidth: 700, lineHeight: 1.6, marginTop: 16 }}>
          Welcome to your unified command center. Monitor sprints, review pull requests, track CI/CD pipelines, 
          and leverage AI-assisted planning—all from a single, powerful interface.
        </p>
        {activeSprint && (
          <div
            style={{
              marginTop: 20,
              padding: "12px 16px",
              background: "rgba(99,102,241,0.2)",
              borderRadius: 10,
              display: "inline-flex",
              alignItems: "center",
              gap: 10,
              fontSize: 13,
              border: "1px solid rgba(99,102,241,0.3)",
            }}
          >
            <Zap size={16} color="var(--accent)" />
            <span style={{ fontWeight: 600 }}>Active Sprint:</span>
            <span style={{ color: "var(--accent)", fontWeight: 600 }}>{activeSprint.name}</span>
            <span style={{ color: "var(--muted)" }}>•</span>
            <span style={{ color: "var(--text)" }}>{completionRate}% complete</span>
            <span style={{ color: "var(--muted)" }}>•</span>
            <span style={{ color: "var(--text)" }}>{metrics.donePoints || 0}/{metrics.totalPoints || 0} points</span>
          </div>
        )}
      </div>

      {/* Key Metrics Grid */}
      <div>
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16, color: "var(--text)", display: "flex", alignItems: "center", gap: 8 }}>
          <BarChart3 size={20} color="var(--accent)" />
          Key Performance Metrics
        </h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: 16,
          }}
        >
          <MetricCard
            icon={Target}
            label="Sprint Velocity"
            value={loading ? "..." : metrics.velocity || 0}
            subtitle="Tickets completed"
            trend={15}
            color="var(--success)"
            loading={loading}
          />
          <MetricCard
            icon={TrendingUp}
            label="Story Points"
            value={loading ? "..." : `${metrics.donePoints || 0}/${metrics.totalPoints || 0}`}
            subtitle={`${completionRate}% completion rate`}
            color="var(--accent)"
            loading={loading}
          />
          <MetricCard
            icon={GitPullRequest}
            label="Open Pull Requests"
            value={loading ? "..." : prs.length}
            subtitle="Awaiting review"
            color="#8b5cf6"
            loading={loading}
          />
          <MetricCard
            icon={Activity}
            label="CI/CD Success"
            value={loading ? "..." : `${metrics.ciSuccessRate || 0}%`}
            subtitle="Last 10 runs"
            trend={8}
            color={metrics.ciSuccessRate >= 80 ? "var(--success)" : "var(--warning)"}
            loading={loading}
          />
        </div>
      </div>

      {/* Sprint Progress & Quick Actions */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "1.5rem",
        }}
      >
        
        {/* Sprint Progress */}
        <div
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            padding: "1.5rem",
          }}
        >
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20, color: "var(--text)", display: "flex", alignItems: "center", gap: 8 }}>
            <Calendar size={18} color="var(--accent)" />
            Current Sprint Progress
          </h3>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 20 }}>
            <ProgressRing percentage={completionRate} color="var(--accent)" />
            <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: 12 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: 13, color: "var(--muted)" }}>Total Issues</span>
                <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text)" }}>{issues.length}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: 13, color: "var(--muted)" }}>Completed</span>
                <span style={{ fontSize: 14, fontWeight: 600, color: "var(--success)" }}>
                  {issues.filter((i) => i.status === "Done").length}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: 13, color: "var(--muted)" }}>In Progress</span>
                <span style={{ fontSize: 14, fontWeight: 600, color: "var(--accent)" }}>
                  {issues.filter((i) => i.status === "In Progress").length}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: 13, color: "var(--muted)" }}>To Do</span>
                <span style={{ fontSize: 14, fontWeight: 600, color: "var(--muted)" }}>
                  {issues.filter((i) => i.status === "To Do").length}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: "var(--text)", display: "flex", alignItems: "center", gap: 8 }}>
            <Zap size={18} color="var(--accent)" />
            Quick Actions
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <QuickActionButton
              icon={Play}
              label="View Sprint Board"
              description="Monitor tickets, run implementation workflows"
              onClick={() => navigateToTab("sprint")}
              color="var(--accent)"
            />
            <QuickActionButton
              icon={MessageSquare}
              label="PM Agent Chat"
              description="AI-powered sprint planning and insights"
              onClick={() => navigateToTab("pm agent")}
              color="#8b5cf6"
            />
            <QuickActionButton
              icon={GitBranch}
              label="CI/CD Workflows"
              description="Monitor GitHub Actions and pipeline status"
              onClick={() => navigateToTab("workflows")}
              color="var(--success)"
            />
            <QuickActionButton
              icon={Rocket}
              label="UAT Deployment"
              description="Deploy to UAT environment"
              onClick={() => navigateToTab("deploy")}
              color="var(--warning)"
            />
          </div>
        </div>
      </div>

      {/* Activity Timeline & System Health */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(380px, 1fr))",
          gap: "1.5rem",
        }}
      >
        
        {/* Recent Activity Timeline */}
        <div>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: "var(--text)", display: "flex", alignItems: "center", gap: 8 }}>
            <Clock size={18} color="var(--accent)" />
            Recent Activity
          </h3>
          <div
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: 12,
              padding: "1.5rem",
              minHeight: 400,
            }}
          >
            {loading ? (
              <div style={{ textAlign: "center", color: "var(--muted)", padding: "3rem 1rem" }}>
                <Activity size={32} style={{ marginBottom: 12, opacity: 0.5 }} />
                <div>Loading activity feed...</div>
              </div>
            ) : recentActivity.length === 0 ? (
              <div style={{ textAlign: "center", color: "var(--muted)", padding: "3rem 1rem" }}>
                <AlertCircle size={32} style={{ marginBottom: 12, opacity: 0.5 }} />
                <div>No recent activity</div>
              </div>
            ) : (
              <div>
                {recentActivity.slice(0, 8).map((activity, idx) => (
                  <ActivityTimelineItem key={idx} {...activity} />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* System Health */}
        <div>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: "var(--text)", display: "flex", alignItems: "center", gap: 8 }}>
            <Activity size={18} color="var(--accent)" />
            System Health
          </h3>
          <div
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: 12,
              padding: "1.5rem",
            }}
          >
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <HealthStatus
                label="CI/CD Pipeline"
                status={ciHealth}
                message={`${metrics.ciSuccessRate || 0}% success rate across recent runs`}
                metric={`${metrics.ciSuccessRate || 0}%`}
              />
              <HealthStatus
                label="Pull Request Queue"
                status={prHealth}
                message={`${prs.length} PRs open and awaiting review or merge`}
                metric={prs.length}
              />
              <HealthStatus
                label="Sprint Velocity"
                status={sprintHealth}
                message={`${metrics.velocity || 0} tickets completed in current sprint`}
                metric={metrics.velocity || 0}
              />
              <HealthStatus
                label="Code Quality"
                status="healthy"
                message="All quality gates passing on latest commits"
                metric="✓"
              />
            </div>
          </div>

          {/* Team Summary */}
          <div
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: 12,
              padding: "1.5rem",
              marginTop: 16,
            }}
          >
            <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: "var(--text)", display: "flex", alignItems: "center", gap: 8 }}>
              <Users size={16} color="var(--accent)" />
              Team Summary
            </h4>
            <div style={{ display: "flex", flexDirection: "column", gap: 10, fontSize: 13 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--muted)" }}>Active Contributors</span>
                <span style={{ color: "var(--text)", fontWeight: 600 }}>
                  {new Set(prs.map((pr) => pr.user?.login)).size}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--muted)" }}>Commits Today</span>
                <span style={{ color: "var(--text)", fontWeight: 600 }}>
                  {runs.filter((r) => {
                    const created = new Date(r.created_at);
                    const today = new Date();
                    return created.toDateString() === today.toDateString();
                  }).length}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--muted)" }}>Workflow Runs</span>
                <span style={{ color: "var(--text)", fontWeight: 600 }}>{runs.length}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Pro Tips */}
      <div
        style={{
          background: "linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(139,92,246,0.1) 100%)",
          border: "1px solid rgba(99,102,241,0.25)",
          borderRadius: 12,
          padding: "1.25rem",
          fontSize: 13,
          display: "flex",
          alignItems: "flex-start",
          gap: 14,
        }}
      >
        <div style={{ fontSize: 24, flexShrink: 0 }}>💡</div>
        <div>
          <div style={{ fontWeight: 700, color: "var(--text)", marginBottom: 6, fontSize: 14 }}>Pro Tips</div>
          <ul style={{ margin: 0, paddingLeft: 20, color: "var(--muted)", lineHeight: 1.8 }}>
            <li>
              Use the <strong style={{ color: "var(--accent)" }}>Sprint Status</strong> tab to trigger automated
              ticket implementation with a single click
            </li>
            <li>
              Chat with the <strong style={{ color: "#8b5cf6" }}>PM Agent</strong> to plan sprints and get
              AI-powered project insights
            </li>
            <li>
              Monitor <strong style={{ color: "var(--success)" }}>GitHub Workflows</strong> for real-time CI/CD
              pipeline status and logs
            </li>
          </ul>
        </div>
      </div>

      {/* CSS Animation for pulse effect */}
      <style>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.6;
          }
        }
      `}</style>
    </div>
  );
};

/**
 * Helper function to format time ago
 */
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

export default OverviewRedesigned;
