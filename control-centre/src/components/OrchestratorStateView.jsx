import React, { useState, useEffect } from "react";
import {
  fetchOrchestratorState,
  resumeOrchestrator,
  clearOrchestratorState,
  checkOrchestratorStatus,
} from "../api/orchestratorApi";
import {
  PlayCircle,
  Trash2,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Clock,
  Activity,
  FileText,
  Server,
} from "lucide-react";

const StateBadge = ({ status }) => {
  const configs = {
    running: { color: "#22c55e", bg: "#22c55e20", label: "Running" },
    crashed: { color: "#ef4444", bg: "#ef444420", label: "Crashed" },
    paused: { color: "#f59e0b", bg: "#f59e0b20", label: "Paused" },
    completed: { color: "#6366f1", bg: "#6366f120", label: "Completed" },
    idle: { color: "#94a3b8", bg: "#94a3b820", label: "Idle" },
  };
  
  const config = configs[status] || configs.idle;
  
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "4px 10px",
        borderRadius: 16,
        background: config.bg,
        color: config.color,
        fontSize: 12,
        fontWeight: 600,
      }}
    >
      <div
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: config.color,
          boxShadow: `0 0 4px ${config.color}`,
        }}
      />
      {config.label}
    </div>
  );
};

const InfoCard = ({ icon: Icon, label, value, color = "var(--accent)" }) => (
  <div
    style={{
      background: "var(--bg-card)",
      border: "1px solid var(--border)",
      borderRadius: 10,
      padding: "1rem",
      display: "flex",
      alignItems: "center",
      gap: 12,
    }}
  >
    <div
      style={{
        width: 40,
        height: 40,
        borderRadius: 8,
        background: `${color}20`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: color,
      }}
    >
      <Icon size={20} />
    </div>
    <div style={{ flex: 1 }}>
      <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 2 }}>
        {label}
      </div>
      <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)" }}>
        {value || "—"}
      </div>
    </div>
  </div>
);

const TicketItem = ({ ticket, status }) => {
  const statusConfig = {
    completed: { color: "#22c55e", icon: CheckCircle2 },
    in_progress: { color: "#3b82f6", icon: Activity },
    pending: { color: "#94a3b8", icon: Clock },
    failed: { color: "#ef4444", icon: AlertCircle },
  };
  
  const config = statusConfig[status] || statusConfig.pending;
  const Icon = config.icon;
  
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "8px 12px",
        background: "var(--bg)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        marginBottom: 6,
      }}
    >
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: 6,
          background: `${config.color}20`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: config.color,
          flexShrink: 0,
        }}
      >
        <Icon size={14} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: 13,
            fontWeight: 500,
            color: "var(--text)",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {ticket.key || ticket}
        </div>
        {ticket.summary && (
          <div
            style={{
              fontSize: 11,
              color: "var(--muted)",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {ticket.summary}
          </div>
        )}
      </div>
      <StateBadge status={status} />
    </div>
  );
};

const OrchestratorStateView = () => {
  const [state, setState] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  const loadData = async () => {
    setLoading(true);
    setMessage(null);
    
    try {
      const [stateData, statusData] = await Promise.all([
        fetchOrchestratorState(),
        checkOrchestratorStatus(),
      ]);
      
      setState(stateData);
      setStatus(statusData);
      setLastRefresh(new Date());
    } catch (error) {
      console.error("Error loading orchestrator data:", error);
      setMessage({
        success: false,
        text: "Failed to load orchestrator data",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const handleResume = async () => {
    setActionLoading(true);
    setMessage(null);
    
    try {
      const result = await resumeOrchestrator();
      setMessage({
        success: result.success,
        text: result.message,
      });
      
      if (result.success) {
        setTimeout(loadData, 1000); // Reload after resume
      }
    } catch (error) {
      setMessage({
        success: false,
        text: "Failed to resume orchestrator",
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleClear = async () => {
    if (!confirm("Are you sure you want to clear the orchestrator state? This cannot be undone.")) {
      return;
    }
    
    setActionLoading(true);
    setMessage(null);
    
    try {
      const result = await clearOrchestratorState();
      setMessage({
        success: result.success,
        text: result.message,
      });
      
      if (result.success) {
        setTimeout(loadData, 500);
      }
    } catch (error) {
      setMessage({
        success: false,
        text: "Failed to clear state",
      });
    } finally {
      setActionLoading(false);
    }
  };

  const hasState = state && Object.keys(state).length > 0;
  const isRunning = status?.running || false;
  
  // Extract useful information from state
  const currentTicket = state?.current_ticket;
  const completedTickets = state?.completed_tickets || [];
  const pendingTickets = state?.pending_tickets || [];
  const timestamp = state?.timestamp;
  const totalTickets = completedTickets.length + pendingTickets.length + (currentTicket ? 1 : 0);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      
      {/* Header */}
      <div
        style={{
          background: "linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(139,92,246,0.1) 100%)",
          border: "1px solid rgba(99,102,241,0.2)",
          borderRadius: 16,
          padding: "2rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 20, marginBottom: 12 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
              <Server size={28} color="var(--accent)" />
              <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0 }}>
                Orchestrator State
              </h1>
            </div>
            <p style={{ fontSize: 14, color: "var(--muted)", margin: 0, maxWidth: 600 }}>
              Monitor and manage the orchestrator's state. Resume from a crash or clear the state to start fresh.
            </p>
          </div>
          
          <button
            onClick={loadData}
            disabled={loading}
            style={{
              background: "var(--accent)",
              color: "white",
              border: "none",
              borderRadius: 8,
              padding: "8px 14px",
              fontSize: 13,
              fontWeight: 500,
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.6 : 1,
              display: "flex",
              alignItems: "center",
              gap: 6,
              flexShrink: 0,
            }}
          >
            <RefreshCw size={14} style={{ animation: loading ? "spin 1s linear infinite" : "none" }} />
            Refresh
          </button>
        </div>
        
        <div
          style={{
            marginTop: 16,
            padding: "8px 12px",
            background: isRunning ? "rgba(34, 197, 94, 0.15)" : "rgba(148, 163, 184, 0.15)",
            borderRadius: 8,
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            fontSize: 12,
          }}
        >
          <Activity size={14} color={isRunning ? "#22c55e" : "#94a3b8"} />
          <span style={{ fontWeight: 500 }}>Status:</span>
          <span style={{ color: isRunning ? "#22c55e" : "#94a3b8", fontWeight: 600 }}>
            {isRunning ? "Running" : "Stopped"}
          </span>
          {status?.message && (
            <>
              <span style={{ color: "var(--muted)" }}>·</span>
              <span style={{ color: "var(--muted)" }}>{status.message}</span>
            </>
          )}
        </div>
      </div>

      {/* Message/Alert */}
      {message && (
        <div
          style={{
            padding: "10px 14px",
            borderRadius: 8,
            fontSize: 13,
            background: message.success ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)",
            color: message.success ? "#22c55e" : "#ef4444",
            border: `1px solid ${message.success ? "rgba(34,197,94,0.2)" : "rgba(239,68,68,0.2)"}`,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          {message.success ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
          {message.text}
        </div>
      )}

      {loading && !state ? (
        <div style={{ textAlign: "center", color: "var(--muted)", padding: "3rem" }}>
          <RefreshCw size={32} style={{ animation: "spin 1s linear infinite", marginBottom: 16 }} />
          <div>Loading orchestrator state...</div>
        </div>
      ) : !hasState ? (
        <div
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            padding: "3rem 2rem",
            textAlign: "center",
          }}
        >
          <FileText size={48} color="var(--muted)" style={{ marginBottom: 16 }} />
          <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>
            No Saved State
          </h3>
          <p style={{ fontSize: 14, color: "var(--muted)", margin: 0 }}>
            The orchestrator has no saved state. State is automatically saved when the orchestrator is running.
          </p>
        </div>
      ) : (
        <>
          {/* Action Buttons */}
          <div style={{ display: "flex", gap: 10 }}>
            <button
              onClick={handleResume}
              disabled={actionLoading || isRunning}
              style={{
                background: isRunning ? "rgba(99,102,241,0.2)" : "var(--accent)",
                color: "white",
                border: "none",
                borderRadius: 8,
                padding: "10px 18px",
                fontSize: 14,
                fontWeight: 500,
                cursor: actionLoading || isRunning ? "not-allowed" : "pointer",
                opacity: actionLoading || isRunning ? 0.6 : 1,
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <PlayCircle size={16} />
              {isRunning ? "Already Running" : "Resume from State"}
            </button>
            
            <button
              onClick={handleClear}
              disabled={actionLoading}
              style={{
                background: "transparent",
                color: "#ef4444",
                border: "1px solid #ef4444",
                borderRadius: 8,
                padding: "10px 18px",
                fontSize: 14,
                fontWeight: 500,
                cursor: actionLoading ? "not-allowed" : "pointer",
                opacity: actionLoading ? 0.6 : 1,
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <Trash2 size={16} />
              Clear State
            </button>
          </div>

          {/* State Overview */}
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: "var(--text)" }}>
              State Overview
            </h2>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                gap: 12,
              }}
            >
              <InfoCard
                icon={FileText}
                label="Total Tickets"
                value={totalTickets}
                color="var(--accent)"
              />
              <InfoCard
                icon={CheckCircle2}
                label="Completed"
                value={completedTickets.length}
                color="#22c55e"
              />
              <InfoCard
                icon={Clock}
                label="Pending"
                value={pendingTickets.length}
                color="#f59e0b"
              />
              <InfoCard
                icon={Activity}
                label="Last Updated"
                value={timestamp ? new Date(timestamp).toLocaleString() : "Unknown"}
                color="#6366f1"
              />
            </div>
          </div>

          {/* Current Ticket */}
          {currentTicket && (
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: "var(--text)" }}>
                Current Ticket
              </h2>
              <TicketItem ticket={currentTicket} status="in_progress" />
            </div>
          )}

          {/* Completed Tickets */}
          {completedTickets.length > 0 && (
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: "var(--text)" }}>
                Completed Tickets ({completedTickets.length})
              </h2>
              <div
                style={{
                  background: "var(--bg-card)",
                  border: "1px solid var(--border)",
                  borderRadius: 12,
                  padding: "1rem",
                  maxHeight: 300,
                  overflowY: "auto",
                }}
              >
                {completedTickets.map((ticket, idx) => (
                  <TicketItem key={idx} ticket={ticket} status="completed" />
                ))}
              </div>
            </div>
          )}

          {/* Pending Tickets */}
          {pendingTickets.length > 0 && (
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: "var(--text)" }}>
                Pending Tickets ({pendingTickets.length})
              </h2>
              <div
                style={{
                  background: "var(--bg-card)",
                  border: "1px solid var(--border)",
                  borderRadius: 12,
                  padding: "1rem",
                  maxHeight: 300,
                  overflowY: "auto",
                }}
              >
                {pendingTickets.map((ticket, idx) => (
                  <TicketItem key={idx} ticket={ticket} status="pending" />
                ))}
              </div>
            </div>
          )}

          {/* Raw State (for debugging) */}
          <details style={{ marginTop: "1rem" }}>
            <summary
              style={{
                cursor: "pointer",
                fontSize: 14,
                fontWeight: 500,
                color: "var(--muted)",
                padding: "8px 0",
              }}
            >
              Show Raw State (Debug)
            </summary>
            <pre
              style={{
                background: "var(--bg)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                padding: "1rem",
                fontSize: 12,
                color: "var(--text)",
                overflow: "auto",
                marginTop: 8,
              }}
            >
              {JSON.stringify(state, null, 2)}
            </pre>
          </details>
        </>
      )}

      {/* Footer info */}
      <div
        style={{
          fontSize: 11,
          color: "var(--muted)",
          textAlign: "center",
          padding: "1rem 0",
        }}
      >
        Last refreshed: {lastRefresh.toLocaleTimeString()} · Auto-refreshes every 30 seconds
      </div>
      
      {/* CSS for spin animation */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default OrchestratorStateView;
