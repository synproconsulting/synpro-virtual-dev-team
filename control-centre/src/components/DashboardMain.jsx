import React, { useState, useEffect } from "react";
import { 
  Activity, 
  GitBranch, 
  CheckCircle2, 
  Clock, 
  TrendingUp,
  Zap,
  Calendar,
  GitPullRequest,
  MessageSquare,
  Rocket,
  BarChart3,
  Cloud,
  RefreshCw
} from "lucide-react";
import { fetchOverviewStats } from "../api/dashboardApi";

const NAVIGATION_CARDS = [
  { 
    id: "sprint", 
    label: "Sprint Status",  
    desc: "View sprint progress, run sprints, review PRs",     
    icon: Activity,
    color: "#6366f1",
    gradient: "linear-gradient(135deg, rgba(99,102,241,0.2) 0%, rgba(99,102,241,0.05) 100%)"
  },
  { 
    id: "workflows", 
    label: "Workflows",      
    desc: "Monitor GitHub Actions runs in real-time",           
    icon: GitBranch,
    color: "#8b5cf6",
    gradient: "linear-gradient(135deg, rgba(139,92,246,0.2) 0%, rgba(139,92,246,0.05) 100%)"
  },
  { 
    id: "deploy", 
    label: "UAT Deploy",     
    desc: "Deploy services to UAT environment",                
    icon: Rocket,
    color: "#ec4899",
    gradient: "linear-gradient(135deg, rgba(236,72,153,0.2) 0%, rgba(236,72,153,0.05) 100%)"
  },
  { 
    id: "sonarcloud", 
    label: "SonarCloud",     
    desc: "Trigger on-demand code quality analysis",           
    icon: BarChart3,
    color: "#14b8a6",
    gradient: "linear-gradient(135deg, rgba(20,184,166,0.2) 0%, rgba(20,184,166,0.05) 100%)"
  },
  { 
    id: "pm-agent", 
    label: "PM Agent",       
    desc: "Chat with the PM Agent to plan sprints",            
    icon: MessageSquare,
    color: "#f59e0b",
    gradient: "linear-gradient(135deg, rgba(245,158,11,0.2) 0%, rgba(245,158,11,0.05) 100%)"
  },
];

const StatusBadge = ({ status, label }) => {
  const colors = {
    operational: { bg: "rgba(34,197,94,0.15)", color: "#22c55e", dot: "#22c55e" },
    degraded: { bg: "rgba(245,158,11,0.15)", color: "#f59e0b", dot: "#f59e0b" },
    down: { bg: "rgba(239,68,68,0.15)", color: "#ef4444", dot: "#ef4444" },
    unknown: { bg: "rgba(100,116,139,0.15)", color: "#64748b", dot: "#64748b" },
  };
  const c = colors[status] || colors.operational;
  
  return (
    <div style={{
      background: c.bg,
      color: c.color,
      padding: "4px 10px",
      borderRadius: 8,
      fontSize: 11,
      fontWeight: 500,
      display: "inline-flex",
      alignItems: "center",
      gap: 6
    }}>
      <div style={{
        width: 6,
        height: 6,
        borderRadius: "50%",
        background: c.dot,
        animation: status === "operational" ? "pulse 2s ease-in-out infinite" : "none"
      }}/>
      {label}
    </div>
  );
};

const MetricCard = ({ icon: Icon, label, value, trend, color, loading }) => (
  <div style={{
    background: "var(--bg-card)",
    border: "1px solid var(--border)",
    borderRadius: 10,
    padding: "1rem",
    display: "flex",
    alignItems: "center",
    gap: 12,
    transition: "border-color 0.2s"
  }}
    onMouseEnter={e => e.currentTarget.style.borderColor = color}
    onMouseLeave={e => e.currentTarget.style.borderColor = "var(--border)"}
  >
    <div style={{
      width: 40,
      height: 40,
      borderRadius: 10,
      background: `${color}20`,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      flexShrink: 0
    }}>
      <Icon size={20} color={color} />
    </div>
    <div style={{ flex: 1, minWidth: 0 }}>
      <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 4 }}>{label}</div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <div style={{ fontSize: 20, fontWeight: 700 }}>
          {loading ? "—" : value}
        </div>
        {trend && !loading && (
          <div style={{ 
            fontSize: 11, 
            color: trend.up ? "#22c55e" : "#ef4444",
            display: "flex",
            alignItems: "center",
            gap: 2
          }}>
            <TrendingUp size={12} style={{ transform: trend.up ? "none" : "rotate(180deg)" }}/>
            {trend.value}
          </div>
        )}
      </div>
    </div>
  </div>
);

const NavigationCard = ({ item, onClick }) => {
  const Icon = item.icon;
  const [isHovered, setIsHovered] = useState(false);
  
  return (
    <div 
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        background: isHovered ? item.gradient : "var(--bg-card)",
        border: `1px solid ${isHovered ? item.color + "40" : "var(--border)"}`,
        borderRadius: 12,
        padding: "1.5rem",
        cursor: "pointer",
        transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
        transform: isHovered ? "translateY(-2px)" : "translateY(0)",
        boxShadow: isHovered ? `0 8px 24px ${item.color}20` : "none"
      }}
    >
      <div style={{
        width: 48,
        height: 48,
        borderRadius: 12,
        background: `${item.color}${isHovered ? "30" : "20"}`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        marginBottom: 12,
        transition: "all 0.2s"
      }}>
        <Icon size={24} color={item.color} strokeWidth={2} />
      </div>
      <div style={{
        fontSize: 15,
        fontWeight: 600,
        marginBottom: 6,
        color: "var(--text)"
      }}>
        {item.label}
      </div>
      <div style={{
        fontSize: 13,
        color: "var(--muted)",
        lineHeight: 1.5
      }}>
        {item.desc}
      </div>
    </div>
  );
};

const QuickAction = ({ icon: Icon, label, onClick, color = "var(--accent)" }) => (
  <button
    onClick={onClick}
    style={{
      background: "var(--bg-card)",
      border: "1px solid var(--border)",
      borderRadius: 10,
      padding: "0.75rem 1rem",
      cursor: "pointer",
      transition: "all 0.15s",
      display: "flex",
      alignItems: "center",
      gap: 10,
      fontSize: 13,
      fontWeight: 500,
      color: "var(--text)",
      fontFamily: "inherit",
      width: "100%"
    }}
    onMouseEnter={e => {
      e.currentTarget.style.borderColor = color;
      e.currentTarget.style.background = `${color}10`;
    }}
    onMouseLeave={e => {
      e.currentTarget.style.borderColor = "var(--border)";
      e.currentTarget.style.background = "var(--bg-card)";
    }}
  >
    <Icon size={16} color={color} />
    {label}
  </button>
);

const DashboardMain = () => {
  const [systemStatus, setSystemStatus] = useState({
    overall: "unknown",
    services: {
      github: "unknown",
      jira: "unknown",
      uat: "unknown"
    }
  });

  const [metrics, setMetrics] = useState({
    activeSprints: 0,
    openPRs: 0,
    activeWorkflows: 0,
    todayDeploys: 0
  });

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const data = await fetchOverviewStats();
      setSystemStatus(data.status);
      setMetrics(data.metrics);
    } catch (error) {
      console.error("Error loading overview data:", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    // Refresh every 60 seconds
    const interval = setInterval(loadData, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const navigateToTab = (tabId) => {
    // Dispatch custom event that App.jsx listens to
    window.dispatchEvent(new CustomEvent('cc-navigate', { detail: tabId }));
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case "operational": return "All Systems Operational";
      case "degraded": return "Some Systems Degraded";
      case "down": return "Systems Down";
      default: return "Checking Status...";
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      
      {/* Hero Section */}
      <div style={{
        background: "linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(139,92,246,0.1) 100%)",
        border: "1px solid rgba(99,102,241,0.2)",
        borderRadius: 12,
        padding: "2rem",
        position: "relative",
        overflow: "hidden"
      }}>
        <div style={{
          position: "absolute",
          top: -50,
          right: -50,
          width: 200,
          height: 200,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(99,102,241,0.2) 0%, transparent 70%)",
          filter: "blur(40px)"
        }}/>
        <div style={{ position: "relative", zIndex: 1 }}>
          <div style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 12,
            flexWrap: "wrap",
            gap: 12
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <Zap size={32} color="#6366f1" strokeWidth={2}/>
              <div>
                <div style={{ fontSize: 28, fontWeight: 700, marginBottom: 4 }}>
                  Welcome to SynPro Control Centre
                </div>
                <div style={{ fontSize: 14, color: "var(--muted)" }}>
                  Manage sprints, deployments, code quality and AI-assisted planning from one place
                </div>
              </div>
            </div>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              style={{
                background: "rgba(99,102,241,0.2)",
                border: "1px solid rgba(99,102,241,0.3)",
                borderRadius: 8,
                padding: "8px 12px",
                cursor: refreshing ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
                fontSize: 12,
                color: "var(--text)",
                fontFamily: "inherit",
                opacity: refreshing ? 0.6 : 1
              }}
            >
              <RefreshCw 
                size={14} 
                style={{ 
                  animation: refreshing ? "spin 1s linear infinite" : "none" 
                }}
              />
              Refresh
            </button>
          </div>
          
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: 16,
            marginTop: 16,
            flexWrap: "wrap"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Clock size={14} color="var(--muted)" />
              <span style={{ fontSize: 12, color: "var(--muted)" }}>
                {new Date().toLocaleDateString('en-US', { 
                  weekday: 'long', 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}
              </span>
            </div>
            <div style={{ width: 1, height: 16, background: "var(--border)" }}/>
            <StatusBadge 
              status={systemStatus.overall} 
              label={getStatusLabel(systemStatus.overall)} 
            />
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: 12
      }}>
        <MetricCard
          icon={Calendar}
          label="Active Sprints"
          value={metrics.activeSprints}
          color="#6366f1"
          loading={loading}
        />
        <MetricCard
          icon={GitPullRequest}
          label="Open PRs"
          value={metrics.openPRs}
          color="#8b5cf6"
          loading={loading}
        />
        <MetricCard
          icon={Activity}
          label="Active Workflows"
          value={metrics.activeWorkflows}
          color="#ec4899"
          loading={loading}
        />
        <MetricCard
          icon={Cloud}
          label="Deployments Today"
          value={metrics.todayDeploys}
          color="#14b8a6"
          loading={loading}
        />
      </div>

      {/* Navigation Grid */}
      <div>
        <div style={{
          fontSize: 16,
          fontWeight: 600,
          marginBottom: 12,
          color: "var(--text)"
        }}>
          Quick Navigation
        </div>
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: 12
        }}>
          {NAVIGATION_CARDS.map(item => (
            <NavigationCard
              key={item.id}
              item={item}
              onClick={() => navigateToTab(item.id)}
            />
          ))}
        </div>
      </div>

      {/* Quick Actions & Tips Row */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: 12
      }}>
        {/* Quick Actions */}
        <div style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          borderRadius: 12,
          padding: "1.25rem"
        }}>
          <div style={{
            fontSize: 14,
            fontWeight: 600,
            marginBottom: 12,
            display: "flex",
            alignItems: "center",
            gap: 8
          }}>
            <Zap size={16} color="var(--accent)" />
            Quick Actions
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <QuickAction
              icon={Activity}
              label="View Current Sprint"
              onClick={() => navigateToTab('sprint')}
              color="#6366f1"
            />
            <QuickAction
              icon={MessageSquare}
              label="Talk to PM Agent"
              onClick={() => navigateToTab('pm-agent')}
              color="#f59e0b"
            />
            <QuickAction
              icon={Rocket}
              label="Deploy to UAT"
              onClick={() => navigateToTab('deploy')}
              color="#ec4899"
            />
          </div>
        </div>

        {/* Tips & Status */}
        <div style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          borderRadius: 12,
          padding: "1.25rem"
        }}>
          <div style={{
            fontSize: 14,
            fontWeight: 600,
            marginBottom: 12,
            display: "flex",
            alignItems: "center",
            gap: 8
          }}>
            <CheckCircle2 size={16} color="#22c55e" />
            System Status
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <div style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              fontSize: 12
            }}>
              <span style={{ color: "var(--muted)" }}>GitHub Integration</span>
              <StatusBadge 
                status={systemStatus.services.github} 
                label={systemStatus.services.github === "operational" ? "Active" : "Checking..."} 
              />
            </div>
            <div style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              fontSize: 12
            }}>
              <span style={{ color: "var(--muted)" }}>Jira Connection</span>
              <StatusBadge 
                status={systemStatus.services.jira} 
                label={systemStatus.services.jira === "operational" ? "Active" : "Checking..."} 
              />
            </div>
            <div style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              fontSize: 12
            }}>
              <span style={{ color: "var(--muted)" }}>UAT Environment</span>
              <StatusBadge 
                status={systemStatus.services.uat} 
                label={systemStatus.services.uat === "operational" ? "Active" : "Checking..."} 
              />
            </div>
          </div>
        </div>
      </div>

      {/* Getting Started Tip */}
      <div style={{
        background: "rgba(99,102,241,0.08)",
        border: "1px solid rgba(99,102,241,0.2)",
        borderRadius: 10,
        padding: "1rem",
        fontSize: 13,
        display: "flex",
        gap: 12,
        alignItems: "flex-start"
      }}>
        <div style={{ fontSize: 20, flexShrink: 0 }}>💡</div>
        <div>
          <div style={{ fontWeight: 600, color: "var(--text)", marginBottom: 4 }}>
            Getting Started
          </div>
          <div style={{ color: "var(--muted)", lineHeight: 1.6 }}>
            Start with <strong style={{ color: "var(--accent)" }}>Sprint Status</strong> to see your current sprint progress and run pending tickets, 
            or use <strong style={{ color: "var(--accent)" }}>PM Agent</strong> to plan a new sprint with AI assistance.
          </div>
        </div>
      </div>

      {/* Animation keyframes */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default DashboardMain;
