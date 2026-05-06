/**
 * SprintStatusOverview.jsx
 * =========================
 * Comprehensive sprint status display component
 * Shows current sprint metrics, health indicators, and team workload
 */

import React, { useState, useEffect } from 'react';
import { fetchCurrentSprintStatus } from '../api/sprintStatusApi';
import { 
  Calendar, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Users,
  Target,
  Activity
} from 'lucide-react';

const SprintStatusOverview = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadStatus = async () => {
    const data = await fetchCurrentSprintStatus();
    if (data) {
      setStatus(data);
      setLastUpdated(new Date(data.last_updated));
    }
    setLoading(false);
  };

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div style={{ padding: "2rem", textAlign: "center", color: "var(--muted)" }}>
        <Activity size={24} style={{ marginBottom: "0.5rem", animation: "spin 1s linear infinite" }} />
        <div>Loading sprint status...</div>
      </div>
    );
  }

  if (!status || !status.sprint) {
    return (
      <div style={{
        padding: "2rem",
        textAlign: "center",
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: 10,
      }}>
        <AlertTriangle size={32} style={{ color: "#f59e0b", marginBottom: "0.5rem" }} />
        <div style={{ fontSize: 16, fontWeight: 500, marginBottom: "0.5rem" }}>
          No Active Sprint
        </div>
        <div style={{ fontSize: 13, color: "var(--muted)" }}>
          Start a sprint in Jira to see status here
        </div>
      </div>
    );
  }

  const { sprint, issue_breakdown, story_points, team_workload, health_metrics } = status;

  // Determine health color
  const getHealthColor = () => {
    if (health_metrics.at_risk) return "#ef4444";
    if (health_metrics.completion_rate >= 70) return "#10b981";
    if (health_metrics.completion_rate >= 40) return "#f59e0b";
    return "#ef4444";
  };

  const healthColor = getHealthColor();

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      {/* Sprint Header */}
      <div style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: 10,
        padding: "1.25rem",
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", flexWrap: "wrap", gap: "1rem" }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
              <Target size={20} style={{ color: "var(--accent)" }} />
              <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0 }}>{sprint.name}</h2>
            </div>
            {sprint.goal && (
              <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: "0.75rem" }}>
                {sprint.goal}
              </div>
            )}
            <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", fontSize: 12, color: "var(--muted)" }}>
              {sprint.start_date && (
                <div style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                  <Calendar size={14} />
                  {new Date(sprint.start_date).toLocaleDateString()}
                </div>
              )}
              {sprint.end_date && (
                <div style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                  <Calendar size={14} />
                  {new Date(sprint.end_date).toLocaleDateString()}
                </div>
              )}
              {health_metrics.days_remaining !== null && (
                <div style={{ display: "flex", alignItems: "center", gap: "0.25rem", fontWeight: 500 }}>
                  <Clock size={14} />
                  {health_metrics.days_remaining} days remaining
                </div>
              )}
            </div>
          </div>
          
          {/* Health Indicator */}
          <div style={{
            padding: "0.75rem 1rem",
            borderRadius: 8,
            background: `${healthColor}15`,
            border: `2px solid ${healthColor}30`,
            textAlign: "center",
            minWidth: 120,
          }}>
            <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: "0.25rem" }}>
              Sprint Health
            </div>
            <div style={{ 
              fontSize: 20, 
              fontWeight: 600, 
              color: healthColor,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "0.25rem"
            }}>
              {health_metrics.at_risk ? (
                <AlertTriangle size={18} />
              ) : (
                <CheckCircle size={18} />
              )}
              {health_metrics.at_risk ? "At Risk" : "On Track"}
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div style={{ 
        display: "grid", 
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", 
        gap: "1rem" 
      }}>
        {/* Completion Rate */}
        <MetricCard
          icon={<TrendingUp size={18} />}
          title="Completion Rate"
          value={`${Math.round(story_points.completion_percentage)}%`}
          subtitle={`${story_points.completed} / ${story_points.total} points`}
          color={healthColor}
          progress={story_points.completion_percentage}
        />

        {/* Issues Done */}
        <MetricCard
          icon={<CheckCircle size={18} />}
          title="Issues Completed"
          value={issue_breakdown.done}
          subtitle={`of ${issue_breakdown.total} total`}
          color="#10b981"
        />

        {/* In Progress */}
        <MetricCard
          icon={<Activity size={18} />}
          title="In Progress"
          value={issue_breakdown.in_progress}
          subtitle={`${story_points.in_progress} story points`}
          color="#3b82f6"
        />

        {/* Velocity */}
        <MetricCard
          icon={<TrendingUp size={18} />}
          title="Velocity"
          value={health_metrics.velocity.toFixed(1)}
          subtitle="points per day"
          color="#8b5cf6"
        />
      </div>

      {/* Progress Bar */}
      <div style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: 10,
        padding: "1rem",
      }}>
        <div style={{ 
          display: "flex", 
          justifyContent: "space-between", 
          marginBottom: "0.5rem",
          fontSize: 12,
          color: "var(--muted)"
        }}>
          <span>Story Points Progress</span>
          <span>{story_points.completed} / {story_points.total} ({Math.round(story_points.completion_percentage)}%)</span>
        </div>
        <div style={{ 
          height: 12, 
          background: "var(--bg)", 
          borderRadius: 6, 
          overflow: "hidden",
          position: "relative"
        }}>
          <div style={{
            height: "100%",
            width: `${story_points.completion_percentage}%`,
            background: `linear-gradient(90deg, ${healthColor}, ${healthColor}dd)`,
            borderRadius: 6,
            transition: "width 0.5s ease",
          }} />
        </div>
        <div style={{ 
          display: "flex", 
          gap: "1rem", 
          marginTop: "0.75rem", 
          fontSize: 11,
          flexWrap: "wrap"
        }}>
          <StatusBadge color="#10b981" label="Done" count={issue_breakdown.done} />
          <StatusBadge color="#3b82f6" label="In Progress" count={issue_breakdown.in_progress} />
          <StatusBadge color="#94a3b8" label="To Do" count={issue_breakdown.todo} />
        </div>
      </div>

      {/* Risk Factors */}
      {health_metrics.risk_factors.length > 0 && (
        <div style={{
          background: "#fef3c7",
          border: "1px solid #fbbf24",
          borderRadius: 10,
          padding: "1rem",
        }}>
          <div style={{ 
            display: "flex", 
            alignItems: "center", 
            gap: "0.5rem", 
            marginBottom: "0.75rem",
            fontSize: 14,
            fontWeight: 600,
            color: "#92400e"
          }}>
            <AlertTriangle size={16} />
            Risk Factors
          </div>
          <ul style={{ 
            margin: 0, 
            paddingLeft: "1.5rem", 
            fontSize: 13, 
            color: "#78350f",
            listStyleType: "disc"
          }}>
            {health_metrics.risk_factors.map((risk, idx) => (
              <li key={idx} style={{ marginBottom: "0.25rem" }}>{risk}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Team Workload */}
      {team_workload.length > 0 && (
        <div style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          borderRadius: 10,
          padding: "1rem",
        }}>
          <div style={{ 
            display: "flex", 
            alignItems: "center", 
            gap: "0.5rem", 
            marginBottom: "1rem",
            fontSize: 14,
            fontWeight: 600
          }}>
            <Users size={16} />
            Team Workload
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {team_workload.map((member, idx) => (
              <TeamMemberCard key={idx} member={member} />
            ))}
          </div>
        </div>
      )}

      {/* Last Updated */}
      {lastUpdated && (
        <div style={{ textAlign: "center", fontSize: 11, color: "var(--muted)" }}>
          Last updated: {lastUpdated.toLocaleTimeString()}
        </div>
      )}
    </div>
  );
};

// Helper Components

const MetricCard = ({ icon, title, value, subtitle, color, progress }) => (
  <div style={{
    background: "var(--bg-card)",
    border: "1px solid var(--border)",
    borderRadius: 10,
    padding: "1rem",
    position: "relative",
    overflow: "hidden"
  }}>
    {progress !== undefined && (
      <div style={{
        position: "absolute",
        bottom: 0,
        left: 0,
        right: 0,
        height: 3,
        background: "var(--bg)",
      }}>
        <div style={{
          height: "100%",
          width: `${progress}%`,
          background: color,
          transition: "width 0.5s ease"
        }} />
      </div>
    )}
    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
      <div style={{ color }}>{icon}</div>
      <div style={{ fontSize: 11, color: "var(--muted)", fontWeight: 500 }}>{title}</div>
    </div>
    <div style={{ fontSize: 24, fontWeight: 600, marginBottom: "0.25rem", color }}>
      {value}
    </div>
    {subtitle && (
      <div style={{ fontSize: 11, color: "var(--muted)" }}>{subtitle}</div>
    )}
  </div>
);

const StatusBadge = ({ color, label, count }) => (
  <div style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
    <div style={{ 
      width: 8, 
      height: 8, 
      borderRadius: "50%", 
      background: color 
    }} />
    <span style={{ color: "var(--muted)" }}>{label}: {count}</span>
  </div>
);

const TeamMemberCard = ({ member }) => {
  const completionRate = member.assigned_points > 0 
    ? (member.completed_points / member.assigned_points * 100) 
    : 0;

  return (
    <div style={{
      background: "var(--bg)",
      border: "1px solid var(--border)",
      borderRadius: 8,
      padding: "0.75rem",
    }}>
      <div style={{ 
        display: "flex", 
        justifyContent: "space-between", 
        alignItems: "center",
        marginBottom: "0.5rem"
      }}>
        <div style={{ fontSize: 13, fontWeight: 500 }}>{member.name}</div>
        <div style={{ fontSize: 11, color: "var(--muted)" }}>
          {member.completed_issues} / {member.assigned_issues} issues
        </div>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
        <div style={{ flex: 1 }}>
          <div style={{ 
            height: 6, 
            background: "var(--border)", 
            borderRadius: 3,
            overflow: "hidden" 
          }}>
            <div style={{
              height: "100%",
              width: `${completionRate}%`,
              background: completionRate >= 70 ? "#10b981" : completionRate >= 40 ? "#f59e0b" : "#ef4444",
              borderRadius: 3,
              transition: "width 0.3s ease"
            }} />
          </div>
        </div>
        <div style={{ fontSize: 11, color: "var(--muted)", minWidth: 80, textAlign: "right" }}>
          {member.completed_points} / {member.assigned_points} pts
        </div>
      </div>
    </div>
  );
};

export default SprintStatusOverview;
