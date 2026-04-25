import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import './GitHubActionsMonitor.css';

const GitHubActionsMonitor = ({ owner, repo, refreshInterval = 30000 }) => {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchWorkflows = async () => {
    try {
      const response = await fetch(
        `/api/github/workflows?owner=${owner}&repo=${repo}`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setWorkflows(data.workflows || []);
      setLastUpdated(new Date());
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
  }, [owner, repo, refreshInterval]);

  const getStatusIcon = (status, conclusion) => {
    if (status === 'in_progress' || status === 'queued') {
      return '🔄';
    }
    if (conclusion === 'success') return '✅';
    if (conclusion === 'failure') return '❌';
    if (conclusion === 'cancelled') return '🚫';
    return '⚪';
  };

  const getStatusClass = (status, conclusion) => {
    if (status === 'in_progress' || status === 'queued') return 'status-running';
    if (conclusion === 'success') return 'status-success';
    if (conclusion === 'failure') return 'status-failure';
    if (conclusion === 'cancelled') return 'status-cancelled';
    return 'status-neutral';
  };

  const formatDuration = (startTime, endTime) => {
    if (!startTime) return 'N/A';
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const seconds = Math.floor((end - start) / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  if (loading) {
    return <div className="github-monitor loading">Loading workflows...</div>;
  }

  if (error) {
    return (
      <div className="github-monitor error">
        <h3>Error Loading Workflows</h3>
        <p>{error}</p>
        <button onClick={fetchWorkflows}>Retry</button>
      </div>
    );
  }

  return (
    <div className="github-monitor">
      <div className="monitor-header">
        <h2>GitHub Actions Monitor</h2>
        <div className="monitor-meta">
          <span className="repo-info">
            {owner}/{repo}
          </span>
          {lastUpdated && (
            <span className="last-updated">
              Updated: {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <button className="refresh-btn" onClick={fetchWorkflows}>
            ↻ Refresh
          </button>
        </div>
      </div>

      {workflows.length === 0 ? (
        <div className="no-workflows">No recent workflow runs found</div>
      ) : (
        <div className="workflows-list">
          {workflows.map((workflow) => (
            <div
              key={workflow.id}
              className={`workflow-card ${getStatusClass(
                workflow.status,
                workflow.conclusion
              )}`}
            >
              <div className="workflow-status">
                <span className="status-icon">
                  {getStatusIcon(workflow.status, workflow.conclusion)}
                </span>
              </div>
              <div className="workflow-details">
                <div className="workflow-name">{workflow.name}</div>
                <div className="workflow-meta">
                  <span className="workflow-branch">🌿 {workflow.branch}</span>
                  <span className="workflow-trigger">⚡ {workflow.event}</span>
                  <span className="workflow-duration">
                    ⏱️ {formatDuration(workflow.created_at, workflow.updated_at)}
                  </span>
                </div>
                <div className="workflow-commit">
                  <span className="commit-message">{workflow.commit_message}</span>
                  <span className="commit-author">by {workflow.author}</span>
                </div>
              </div>
              <div className="workflow-actions">
                <a
                  href={workflow.html_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="view-link"
                >
                  View →
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

GitHubActionsMonitor.propTypes = {
  owner: PropTypes.string.isRequired,
  repo: PropTypes.string.isRequired,
  refreshInterval: PropTypes.number,
};

export default GitHubActionsMonitor;
