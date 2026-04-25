import React, { useState, useEffect } from 'react';
import './GitHubActionsMonitor.css';

const GitHubActionsMonitor = ({ repoOwner, repoName, refreshInterval = 30000 }) => {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchWorkflows = async () => {
    try {
      const response = await fetch(
        `/api/github/workflows?owner=${repoOwner}&repo=${repoName}`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setWorkflows(data.workflows || []);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflows();
    const interval = setInterval(fetchWorkflows, refreshInterval);
    return () => clearInterval(interval);
  }, [repoOwner, repoName, refreshInterval]);

  const getStatusIcon = (status, conclusion) => {
    if (status === 'in_progress' || status === 'queued') {
      return '🔄';
    }
    if (conclusion === 'success') return '✅';
    if (conclusion === 'failure') return '❌';
    if (conclusion === 'cancelled') return '⚠️';
    return '⏸️';
  };

  const getStatusClass = (status, conclusion) => {
    if (status === 'in_progress') return 'status-running';
    if (status === 'queued') return 'status-queued';
    if (conclusion === 'success') return 'status-success';
    if (conclusion === 'failure') return 'status-failure';
    if (conclusion === 'cancelled') return 'status-cancelled';
    return 'status-unknown';
  };

  const formatDuration = (startTime, endTime) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const seconds = Math.floor((end - start) / 1000);
    
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  if (loading) {
    return <div className="github-actions-monitor loading">Loading workflows...</div>;
  }

  if (error) {
    return (
      <div className="github-actions-monitor error">
        <h3>Error loading workflows</h3>
        <p>{error}</p>
        <button onClick={fetchWorkflows}>Retry</button>
      </div>
    );
  }

  return (
    <div className="github-actions-monitor">
      <div className="monitor-header">
        <h2>GitHub Actions - {repoOwner}/{repoName}</h2>
        <div className="header-controls">
          <span className="last-update">
            Last updated: {lastUpdate?.toLocaleTimeString()}
          </span>
          <button onClick={fetchWorkflows} className="refresh-btn">
            ↻ Refresh
          </button>
        </div>
      </div>

      {workflows.length === 0 ? (
        <div className="no-workflows">No workflow runs found</div>
      ) : (
        <div className="workflows-list">
          {workflows.map((workflow) => (
            <div
              key={workflow.id}
              className={`workflow-card ${getStatusClass(workflow.status, workflow.conclusion)}`}
            >
              <div className="workflow-header">
                <span className="status-icon">
                  {getStatusIcon(workflow.status, workflow.conclusion)}
                </span>
                <div className="workflow-info">
                  <h3>{workflow.name}</h3>
                  <p className="workflow-branch">
                    {workflow.head_branch} • {workflow.event}
                  </p>
                </div>
                <div className="workflow-meta">
                  <span className="workflow-duration">
                    {formatDuration(workflow.created_at, workflow.updated_at)}
                  </span>
                </div>
              </div>

              <div className="workflow-details">
                <div className="detail-item">
                  <span className="detail-label">Commit:</span>
                  <span className="detail-value">
                    {workflow.head_sha?.substring(0, 7)}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Started:</span>
                  <span className="detail-value">
                    {formatTimestamp(workflow.created_at)}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Run #:</span>
                  <span className="detail-value">{workflow.run_number}</span>
                </div>
              </div>

              {workflow.html_url && (
                <a
                  href={workflow.html_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="workflow-link"
                >
                  View on GitHub →
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default GitHubActionsMonitor;
