import React, { useState, useEffect } from 'react';
import {
  getRailwayProjects,
  getEnvironmentDeployments,
  triggerDeployment,
  formatDeploymentStatus,
  checkRailwayHealth
} from '../api/railway';
import './UATDeployment.css';

const UATDeployment = () => {
  const [loading, setLoading] = useState(false);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [deploymentsLoading, setDeploymentsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState('');
  const [deployments, setDeployments] = useState([]);
  const [environmentName, setEnvironmentName] = useState('production');
  const [railwayHealth, setRailwayHealth] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);

  // Load Railway projects and health on mount
  useEffect(() => {
    loadInitialData();
  }, []);

  // Auto-refresh deployments every 30 seconds if enabled
  useEffect(() => {
    let interval;
    if (autoRefresh && selectedProject) {
      interval = setInterval(() => {
        loadDeployments(selectedProject, environmentName, true);
      }, 30000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh, selectedProject, environmentName]);

  const loadInitialData = async () => {
    setProjectsLoading(true);
    setError(null);
    
    try {
      // Check Railway health
      const health = await checkRailwayHealth();
      setRailwayHealth(health);

      if (!health.configured) {
        setError('Railway API is not configured. Please set RAILWAY_API_TOKEN environment variable.');
        setProjectsLoading(false);
        return;
      }

      // Load projects
      const projectsData = await getRailwayProjects();
      setProjects(projectsData.projects || []);

      // Auto-select first project if available and get Railway project ID from env
      const defaultProjectId = import.meta.env.VITE_RAILWAY_PROJECT_ID;
      if (defaultProjectId && projectsData.projects.some(p => p.id === defaultProjectId)) {
        setSelectedProject(defaultProjectId);
        loadDeployments(defaultProjectId, environmentName);
      } else if (projectsData.projects.length > 0) {
        const firstProject = projectsData.projects[0].id;
        setSelectedProject(firstProject);
        loadDeployments(firstProject, environmentName);
      }
    } catch (err) {
      console.error('Failed to load initial data:', err);
      setError(err.message || 'Failed to load Railway data');
    } finally {
      setProjectsLoading(false);
    }
  };

  const loadDeployments = async (projectId, envName, silent = false) => {
    if (!silent) {
      setDeploymentsLoading(true);
    }
    setError(null);

    try {
      const data = await getEnvironmentDeployments(projectId, envName);
      setDeployments(data.deployments || []);
      setLastRefresh(new Date());
    } catch (err) {
      console.error('Failed to load deployments:', err);
      if (!silent) {
        setError(err.message || 'Failed to load deployments');
      }
    } finally {
      if (!silent) {
        setDeploymentsLoading(false);
      }
    }
  };

  const handleProjectChange = (e) => {
    const projectId = e.target.value;
    setSelectedProject(projectId);
    if (projectId) {
      loadDeployments(projectId, environmentName);
    } else {
      setDeployments([]);
    }
  };

  const handleEnvironmentChange = (e) => {
    const envName = e.target.value;
    setEnvironmentName(envName);
    if (selectedProject) {
      loadDeployments(selectedProject, envName);
    }
  };

  const handleRefresh = () => {
    if (selectedProject) {
      loadDeployments(selectedProject, environmentName);
    }
  };

  const handleTriggerDeployment = async (serviceId, environmentId) => {
    setLoading(true);
    setError(null);

    try {
      const result = await triggerDeployment(serviceId, environmentId);
      // Refresh deployments after triggering
      setTimeout(() => {
        if (selectedProject) {
          loadDeployments(selectedProject, environmentName);
        }
      }, 2000);
      return result;
    } catch (err) {
      console.error('Failed to trigger deployment:', err);
      setError(err.message || 'Failed to trigger deployment');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getTimeSince = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  if (projectsLoading) {
    return (
      <div className="uat-deployment-container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading Railway projects...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="uat-deployment-container">
      <div className="uat-deployment-header">
        <div>
          <h2>Railway UAT Deployment Monitor</h2>
          <p className="subtitle">Monitor and manage deployments on Railway</p>
        </div>
        {railwayHealth && (
          <div className={`health-badge ${railwayHealth.status}`}>
            <span className="health-dot"></span>
            {railwayHealth.status === 'healthy' ? 'Connected' : 'Disconnected'}
          </div>
        )}
      </div>

      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="deployment-controls">
        <div className="control-group">
          <label htmlFor="project-select">Project:</label>
          <select
            id="project-select"
            value={selectedProject}
            onChange={handleProjectChange}
            disabled={projects.length === 0}
          >
            <option value="">Select a project</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="environment-select">Environment:</label>
          <select
            id="environment-select"
            value={environmentName}
            onChange={handleEnvironmentChange}
            disabled={!selectedProject}
          >
            <option value="production">Production</option>
            <option value="staging">Staging</option>
            <option value="uat">UAT</option>
            <option value="development">Development</option>
          </select>
        </div>

        <div className="control-actions">
          <button
            onClick={handleRefresh}
            disabled={!selectedProject || deploymentsLoading}
            className="btn-secondary"
          >
            {deploymentsLoading ? 'Refreshing...' : '🔄 Refresh'}
          </button>

          <label className="auto-refresh-toggle">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              disabled={!selectedProject}
            />
            <span>Auto-refresh (30s)</span>
          </label>
        </div>
      </div>

      {lastRefresh && (
        <div className="last-refresh">
          Last updated: {formatDate(lastRefresh)} ({getTimeSince(lastRefresh)})
        </div>
      )}

      {deploymentsLoading && deployments.length === 0 ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading deployments...</p>
        </div>
      ) : deployments.length === 0 ? (
        <div className="empty-state">
          <p>
            {selectedProject
              ? `No deployments found in ${environmentName} environment`
              : 'Select a project to view deployments'}
          </p>
        </div>
      ) : (
        <div className="deployments-grid">
          {deployments.map((deployment) => {
            const statusInfo = formatDeploymentStatus(deployment.status);
            return (
              <div key={deployment.id} className="deployment-card">
                <div className="deployment-header">
                  <h3>{deployment.serviceName || 'Unknown Service'}</h3>
                  <span
                    className="status-badge"
                    style={{ backgroundColor: statusInfo.color }}
                  >
                    {statusInfo.label}
                  </span>
                </div>

                <div className="deployment-details">
                  <div className="detail-row">
                    <span className="detail-label">Deployment ID:</span>
                    <span className="detail-value monospace">
                      {deployment.id.substring(0, 8)}...
                    </span>
                  </div>

                  <div className="detail-row">
                    <span className="detail-label">Created:</span>
                    <span className="detail-value">
                      {formatDate(deployment.createdAt)}
                    </span>
                  </div>

                  {deployment.updatedAt && (
                    <div className="detail-row">
                      <span className="detail-label">Updated:</span>
                      <span className="detail-value">
                        {formatDate(deployment.updatedAt)}
                      </span>
                    </div>
                  )}

                  {deployment.staticUrl && (
                    <div className="detail-row">
                      <span className="detail-label">URL:</span>
                      <a
                        href={deployment.staticUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="detail-link"
                      >
                        {deployment.staticUrl}
                      </a>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default UATDeployment;
