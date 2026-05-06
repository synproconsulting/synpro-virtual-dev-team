/**
 * OrchestratorControl.jsx
 * =======================
 * Control panel for orchestrator state persistence and resume functionality.
 * 
 * Features:
 * - View and resume paused/failed sprint executions
 * - Real-time progress monitoring
 * - Pause/cancel running executions
 * - View detailed state including ticket lists
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  listResumable, 
  getProgress, 
  getState, 
  resumeSprint, 
  pauseSprint, 
  cancelSprint 
} from '../api/orchestratorApi';
import { Play, Pause, X, RefreshCw, ChevronDown, ChevronUp, Clock, CheckCircle, AlertCircle } from 'lucide-react';

const StatusBadge = ({ status }) => {
  const colors = {
    pending: { bg: "rgba(100,116,139,0.15)", text: "var(--muted)" },
    running: { bg: "rgba(99,102,241,0.15)", text: "var(--accent)" },
    paused: { bg: "rgba(245,158,11,0.15)", text: "var(--warning)" },
    failed: { bg: "rgba(239,68,68,0.15)", text: "var(--danger)" },
    completed: { bg: "rgba(34,197,94,0.15)", text: "var(--success)" },
    cancelled: { bg: "rgba(100,116,139,0.15)", text: "var(--muted)" },
  };
  
  const style = colors[status] || colors.pending;
  
  return (
    <span className="badge" style={{ background: style.bg, color: style.text }}>
      {status.toUpperCase()}
    </span>
  );
};

const ProgressBar = ({ percentage, completed, failed, remaining, total }) => {
  const completedPct = (completed / total) * 100;
  const failedPct = (failed / total) * 100;
  
  return (
    <div>
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        fontSize: 12,
        color: "var(--muted)",
        marginBottom: 8
      }}>
        <span>{completed}/{total} completed</span>
        <span>{Math.round(percentage)}%</span>
      </div>
      <div style={{
        height: 8,
        background: "var(--bg)",
        borderRadius: 4,
        overflow: "hidden",
        display: "flex"
      }}>
        <div style={{
          width: `${completedPct}%`,
          background: "var(--success)",
          transition: "width 0.3s"
        }}/>
        <div style={{
          width: `${failedPct}%`,
          background: "var(--danger)",
          transition: "width 0.3s"
        }}/>
      </div>
      <div style={{
        display: "flex",
        gap: 16,
        marginTop: 8,
        fontSize: 11,
        color: "var(--muted)"
      }}>
        <span style={{ color: "var(--success)" }}>
          <CheckCircle size={12} style={{ display: "inline", marginRight: 4 }} />
          {completed} completed
        </span>
        {failed > 0 && (
          <span style={{ color: "var(--danger)" }}>
            <AlertCircle size={12} style={{ display: "inline", marginRight: 4 }} />
            {failed} failed
          </span>
        )}
        <span style={{ color: "var(--muted)" }}>
          <Clock size={12} style={{ display: "inline", marginRight: 4 }} />
          {remaining} remaining
        </span>
      </div>
    </div>
  );
};

const StateCard = ({ state, onRefresh }) => {
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [detailState, setDetailState] = useState(null);
  const [progressData, setProgressData] = useState(null);
  const [message, setMessage] = useState(null);

  const loadDetails = useCallback(async () => {
    if (!state.state_id) return;
    try {
      const [details, progress] = await Promise.all([
        getState(state.state_id),
        getProgress(state.state_id)
      ]);
      setDetailState(details);
      setProgressData(progress);
    } catch (error) {
      console.error("Failed to load state details:", error);
    }
  }, [state.state_id]);

  useEffect(() => {
    if (expanded && !detailState) {
      loadDetails();
    }
  }, [expanded, detailState, loadDetails]);

  const handleResume = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const result = await resumeSprint(state.state_id, "SDT1"); // TODO: make project key dynamic
      setMessage({ type: "success", text: result.message });
      await loadDetails();
      if (onRefresh) onRefresh();
    } catch (error) {
      setMessage({ type: "error", text: error.message });
    } finally {
      setLoading(false);
    }
  };

  const handlePause = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const result = await pauseSprint(state.state_id, "Paused by user");
      setMessage({ type: "success", text: result.message });
      await loadDetails();
      if (onRefresh) onRefresh();
    } catch (error) {
      setMessage({ type: "error", text: error.message });
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm("Are you sure you want to cancel this sprint execution? This cannot be undone.")) {
      return;
    }
    setLoading(true);
    setMessage(null);
    try {
      const result = await cancelSprint(state.state_id, "Cancelled by user");
      setMessage({ type: "success", text: result.message });
      await loadDetails();
      if (onRefresh) onRefresh();
    } catch (error) {
      setMessage({ type: "error", text: error.message });
    } finally {
      setLoading(false);
    }
  };

  const canResume = state.status === "paused" || state.status === "failed";
  const canPause = state.status === "running";
  const canCancel = state.status === "running" || state.status === "paused";

  return (
    <div className="card" style={{ marginBottom: 12 }}>
      {/* Header */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: expanded ? 16 : 0
      }}>
        <div style={{ flex: 1 }}>
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            marginBottom: 6
          }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, margin: 0 }}>
              {state.sprint_name}
            </h3>
            <StatusBadge status={state.status} />
          </div>
          <div style={{ fontSize: 12, color: "var(--muted)" }}>
            Sprint ID: {state.sprint_id} • 
            {state.completed}/{state.total_tickets} tickets completed •
            Last updated: {new Date(state.last_updated).toLocaleString()}
          </div>
        </div>
        
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {canResume && (
            <button
              onClick={handleResume}
              disabled={loading}
              className="btn-primary"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                opacity: loading ? 0.6 : 1
              }}
            >
              <Play size={14} />
              Resume
            </button>
          )}
          {canPause && (
            <button
              onClick={handlePause}
              disabled={loading}
              className="btn-primary"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                background: "var(--warning)",
                opacity: loading ? 0.6 : 1
              }}
            >
              <Pause size={14} />
              Pause
            </button>
          )}
          {canCancel && (
            <button
              onClick={handleCancel}
              disabled={loading}
              className="btn-primary"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                background: "var(--danger)",
                opacity: loading ? 0.6 : 1
              }}
            >
              <X size={14} />
              Cancel
            </button>
          )}
          <button
            onClick={() => setExpanded(!expanded)}
            style={{
              background: "transparent",
              border: "1px solid var(--border)",
              borderRadius: 6,
              padding: "6px 8px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              color: "var(--muted)"
            }}
          >
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div style={{
          marginTop: 12,
          padding: "8px 12px",
          borderRadius: 6,
          fontSize: 12,
          background: message.type === "success" 
            ? "rgba(34,197,94,0.1)" 
            : "rgba(239,68,68,0.1)",
          color: message.type === "success" 
            ? "var(--success)" 
            : "var(--danger)",
          border: `1px solid ${message.type === "success" 
            ? "rgba(34,197,94,0.2)" 
            : "rgba(239,68,68,0.2)"}`
        }}>
          {message.text}
        </div>
      )}

      {/* Expanded Details */}
      {expanded && (
        <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid var(--border)" }}>
          {!detailState || !progressData ? (
            <div style={{ textAlign: "center", padding: "1rem", color: "var(--muted)" }}>
              Loading details...
            </div>
          ) : (
            <>
              {/* Progress Bar */}
              <div style={{ marginBottom: 20 }}>
                <ProgressBar
                  percentage={progressData.progress_percentage}
                  completed={progressData.completed_tickets}
                  failed={progressData.failed_tickets}
                  remaining={progressData.remaining_tickets}
                  total={progressData.total_tickets}
                />
              </div>

              {/* Current Ticket */}
              {detailState.current_ticket && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6, color: "var(--muted)" }}>
                    Current Ticket
                  </div>
                  <div style={{
                    background: "var(--bg)",
                    padding: "8px 12px",
                    borderRadius: 6,
                    fontSize: 13,
                    color: "var(--accent)"
                  }}>
                    {detailState.current_ticket}
                  </div>
                </div>
              )}

              {/* Ticket Lists */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
                {/* Queue */}
                <div>
                  <div style={{
                    fontSize: 12,
                    fontWeight: 600,
                    marginBottom: 8,
                    color: "var(--muted)"
                  }}>
                    Queue ({detailState.ticket_queue?.length || 0})
                  </div>
                  <div style={{
                    background: "var(--bg)",
                    borderRadius: 6,
                    maxHeight: 200,
                    overflowY: "auto",
                    fontSize: 12
                  }}>
                    {(detailState.ticket_queue || []).map((ticket, idx) => (
                      <div key={idx} style={{
                        padding: "6px 10px",
                        borderBottom: idx < detailState.ticket_queue.length - 1 
                          ? "1px solid var(--border)" 
                          : "none"
                      }}>
                        {ticket}
                      </div>
                    ))}
                    {!detailState.ticket_queue?.length && (
                      <div style={{ padding: "12px", color: "var(--muted)", textAlign: "center" }}>
                        Empty
                      </div>
                    )}
                  </div>
                </div>

                {/* Completed */}
                <div>
                  <div style={{
                    fontSize: 12,
                    fontWeight: 600,
                    marginBottom: 8,
                    color: "var(--success)"
                  }}>
                    Completed ({detailState.completed_tickets?.length || 0})
                  </div>
                  <div style={{
                    background: "var(--bg)",
                    borderRadius: 6,
                    maxHeight: 200,
                    overflowY: "auto",
                    fontSize: 12
                  }}>
                    {(detailState.completed_tickets || []).map((ticket, idx) => (
                      <div key={idx} style={{
                        padding: "6px 10px",
                        borderBottom: idx < detailState.completed_tickets.length - 1 
                          ? "1px solid var(--border)" 
                          : "none",
                        color: "var(--success)"
                      }}>
                        ✓ {ticket}
                      </div>
                    ))}
                    {!detailState.completed_tickets?.length && (
                      <div style={{ padding: "12px", color: "var(--muted)", textAlign: "center" }}>
                        None
                      </div>
                    )}
                  </div>
                </div>

                {/* Failed */}
                <div>
                  <div style={{
                    fontSize: 12,
                    fontWeight: 600,
                    marginBottom: 8,
                    color: "var(--danger)"
                  }}>
                    Failed ({detailState.failed_tickets?.length || 0})
                  </div>
                  <div style={{
                    background: "var(--bg)",
                    borderRadius: 6,
                    maxHeight: 200,
                    overflowY: "auto",
                    fontSize: 12
                  }}>
                    {(detailState.failed_tickets || []).map((failure, idx) => (
                      <div key={idx} style={{
                        padding: "6px 10px",
                        borderBottom: idx < detailState.failed_tickets.length - 1 
                          ? "1px solid var(--border)" 
                          : "none",
                        color: "var(--danger)"
                      }}>
                        <div>✗ {failure.ticket_key}</div>
                        <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>
                          {failure.error_message}
                        </div>
                      </div>
                    ))}
                    {!detailState.failed_tickets?.length && (
                      <div style={{ padding: "12px", color: "var(--muted)", textAlign: "center" }}>
                        None
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Error Message */}
              {detailState.error_message && (
                <div style={{
                  marginTop: 16,
                  padding: "10px 12px",
                  borderRadius: 6,
                  fontSize: 12,
                  background: "rgba(239,68,68,0.1)",
                  color: "var(--danger)",
                  border: "1px solid rgba(239,68,68,0.2)"
                }}>
                  <strong>Error:</strong> {detailState.error_message}
                </div>
              )}

              {/* Timestamps */}
              <div style={{
                marginTop: 16,
                display: "grid",
                gridTemplateColumns: "1fr 1fr 1fr",
                gap: 12,
                fontSize: 11,
                color: "var(--muted)"
              }}>
                {detailState.started_at && (
                  <div>
                    <strong>Started:</strong><br/>
                    {new Date(detailState.started_at).toLocaleString()}
                  </div>
                )}
                {detailState.last_checkpoint_at && (
                  <div>
                    <strong>Last Checkpoint:</strong><br/>
                    {new Date(detailState.last_checkpoint_at).toLocaleString()}
                  </div>
                )}
                {detailState.completed_at && (
                  <div>
                    <strong>Completed:</strong><br/>
                    {new Date(detailState.completed_at).toLocaleString()}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

const OrchestratorControl = () => {
  const [states, setStates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadStates = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listResumable();
      setStates(result.states || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStates();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadStates, 30000);
    return () => clearInterval(interval);
  }, [loadStates]);

  return (
    <div>
      {/* Header */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: 20
      }}>
        <div>
          <h2 style={{ fontSize: 24, fontWeight: 700, margin: 0, marginBottom: 6 }}>
            Orchestrator State Management
          </h2>
          <p style={{ color: "var(--muted)", fontSize: 14, margin: 0 }}>
            Resume interrupted sprint executions and monitor progress
          </p>
        </div>
        <button
          onClick={loadStates}
          disabled={loading}
          className="btn-primary"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            opacity: loading ? 0.6 : 1
          }}
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="card" style={{
          background: "rgba(239,68,68,0.1)",
          borderColor: "rgba(239,68,68,0.2)",
          color: "var(--danger)",
          marginBottom: 20
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Loading */}
      {loading && states.length === 0 && (
        <div style={{ textAlign: "center", padding: "3rem", color: "var(--muted)" }}>
          Loading orchestrator states...
        </div>
      )}

      {/* Empty State */}
      {!loading && states.length === 0 && !error && (
        <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>🎯</div>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
            No Resumable States
          </h3>
          <p style={{ color: "var(--muted)", fontSize: 14 }}>
            All sprint executions are either completed or cancelled.
            <br/>
            Paused or failed states will appear here.
          </p>
        </div>
      )}

      {/* State Cards */}
      {states.length > 0 && (
        <div>
          <div style={{
            fontSize: 13,
            color: "var(--muted)",
            marginBottom: 12,
            fontWeight: 500
          }}>
            {states.length} resumable state{states.length !== 1 ? 's' : ''} found
          </div>
          {states.map(state => (
            <StateCard
              key={state.state_id}
              state={state}
              onRefresh={loadStates}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default OrchestratorControl;
