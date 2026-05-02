import React, { useState, useEffect } from 'react';
import {
  getRailwayProjects,
  getProjectServices,
  getProjectEnvironments,
  getServiceDeployments,
  triggerDeployment,
  getDeploymentStatus,
  checkRailwayHealth
} from '../api/railwayApi';
import './UATDeployment.css';

const UATDeployment = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Railway data
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState('');
  const [services, setServices] = useState([]);
  const [environments, setEnvironments] = useState([]);
  const [selectedEnvironment, setSelectedEnvironment] = useState('');
  const [selectedServices, setSelectedServices] = useState([]);
  
  // Deployment tracking
  const [deployments, setDeployments] = useState([]);
  const [pollingDeployments, setPollingDeployments] = useState(new Set());
  
  // Health check
  const [railwayHealthy, setRailwayHealthy] = useState(null);

  // Check Railway API health on mount
  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const health = await checkRailwayHealth();
      setRailwayHealthy(health.status === 'healthy');
      if (health.status !== 'healthy') {
        setError(`Railway API: ${health.message}`);
      }
    } catch (err) {
      setRailwayHealthy(false);
      setError('Failed to check Railway API health');
    }
  };

  // Load projects on mount
  useEffect(() => {
    loadProjects();
  }, []);

  // Load services and environments when project changes
  useEffect(() => {
    if (selectedProject) {
      loadProjectData(selectedProject);
    } else {
      setServices([]);
      setEnvironments([]);
      setSelectedServices([]);
    }
  }, [selectedProject]);

  // Poll deployment status
  useEffect(() => {
    if (pollingDeployments.size === 0) return;

    const interval = setInterval(() => {
      pollingDeployments.forEach(deploymentId => {
        pollDeploymentStatus(deploymentId);
      });
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(interval);
  }, [pollingDeployments]);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const projectsData = await getRailwayProjects();
      setProjects(projectsData);
      
      // Auto-select first project if available
      if (projectsData.length > 0) {
        setSelectedProject(projectsData[0].id);
      }
    } catch (err) {
      setError(`Failed to load projects: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const loadProjectData = async (projectId) => {
    try {
      setLoading(true);
      const [servicesData, environmentsData] = await Promise.all([
        getProjectServices(projectId),
        getProjectEnvironments(projectId)
      ]);
      
      setServices(servicesData);
      setEnvironments(environmentsData);
      
      // Auto-select UAT environment if available
      const uatEnv = environmentsData.find(e => 
        e.name.toLowerCase().includes('uat') || e.name.toLowerCase().includes('staging')
      );
      if (uatEnv) {
        setSelectedEnvironment(uatEnv.id);
      } else if (environmentsData.length > 0) {
        setSelectedEnvironment(environmentsData[0].id);
      }
    } catch (err) {
      setError(`Failed to load project data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleServiceToggle = (serviceId) => {
    setSelectedServices(prev => {
      if (prev.includes(serviceId)) {
        return prev.filter(id => id !== serviceId);
      } else {
        return [...prev, serviceId];
      }
    });
  };

  const handleSelectAll = () => {
    if (selectedServices.length === services.length) {
      setSelectedServices([]);
    } else {
      setSelectedServices(services.map(s => s.id));
    }
  };

  const handleDeploy = async () => {
    if (!selectedEnvironment || selectedServices.length === 0) {
      setError('Please select an environment and at least one service');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const deploymentResults = [];
      
      // Trigger deployment for each selected service
      for (const serviceId of selectedServices) {
        try {
          const result = await triggerDeployment(serviceId, selectedEnvironment);
          deploymentResults.push({
            serviceId,
            serviceName: services.find(s => s.id === serviceId)?.name || 'Unknown',
            deployment: result,
            status: 'triggered'
          });
          
          // Start polling this deployment
          setPollingDeployments(prev => new Set([...prev, result.id]));
        } catch (err) {
          deploymentResults.push({
            serviceId,
            serviceName: services.find(s => s.id === serviceId)?.name || 'Unknown',
            error: err.message,
            status: 'failed'
          });
        }
      }
      
      setDeployments(deploymentResults);
      setSuccess(`Triggered ${deploymentResults.length} deployment(s)`);
    } catch (err) {
      setError(`Deployment failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const pollDeploymentStatus = async (deploymentId) => {
    try {
      const status = await getDeploymentStatus(deploymentId);
      
      // Update deployment status in the list
      setDeployments(prev => prev.map(d => {
        if (d.deployment?.id === deploymentId) {
          return { ...d, deployment: status };
        }
        return d;
      }));
      
      // Stop polling if deployment is complete
      if (['SUCCESS', 'FAILED', 'CRASHED'].includes(status.status)) {
        setPollingDeployments(prev => {
          const next = new Set(prev);
          next.delete(deploymentId);
          return next;
        });
      }
    } catch (err) {
      console.error(`Failed to poll deployment ${deploymentId}:`, err);
    }
  };

  const loadServiceHistory = async (serviceId) => {
    try {
      const history = await getServiceDeployments(serviceId, 5);
      console.log('Deployment history:', history);
      // You can display this in a modal or expand the service card
    } catch (err) {
      console.error('Failed to load service history:', err);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'SUCCESS':
      case 'ACTIVE':
        return '#22c55e';
      case 'BUILDING':
      case 'DEPLOYING':
      case 'INITIALIZING':
        return '#3b82f6';
      case 'FAILED':
      case 'CRASHED':
        return '#ef4444';
      case 'QUEUED':
        return '#f59e0b';
      default:
        return '#6b7280';
    }
  };

  const isFormValid = () => {
    return selectedProject && selectedEnvironment && selectedServices.length > 0;
  };

  return (
    <div className="uat-deployment-container">
      <div className="uat-deployment-header">
        <h2>Railway UAT Deployment</h2>
        <p className="subtitle">Deploy services to Railway environments</p>
        {railwayHealthy === false && (
          <div className="health-warning">
            ⚠️ Railway API is not configured or unreachable
          </div>
        )}
      </div>

      <div className="uat-deployment-form">
        {/* Project Selection */}
        <div className="form-section">
          <h3>Project Configuration</h3>
          <div className="form-group">
            <label htmlFor="project">Railway Project</label>
            <select
              id="project"
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              disabled={loading || projects.length === 0}
            >
              <option value="">Select a project...</option>
              {projects.map(project => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
            {projects.length === 0 && !loading && (
              <small className="form-hint">No projects available</small>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="environment">Environment</label>
            <select
              id="environment"
              value={selectedEnvironment}
              onChange={(e) => setSelectedEnvironment(e.target.value)}
              disabled={loading || environments.length === 0}
            >
              <option value="">Select an environment...</option>
              {environments.map(env => (
                <option key={env.id} value={env.id}>
                  {env.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Service Selection */}
        {services.length > 0 && (
          <div className="form-section">
            <div className="services-header">
              <h3>Select Services to Deploy</h3>
              <button
                type="button"
                onClick={handleSelectAll}
                className="select-all-btn"
                disabled={loading}
              >
                {selectedServices.length === services.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>

            <div className="services-grid">
              {services.map(service => (
                <div
                  key={service.id}
                  className={`service-card ${
                    selectedServices.includes(service.id) ? 'selected' : ''
                  }`}
                  onClick={() => !loading && handleServiceToggle(service.id)}
                >
                  <div className="service-checkbox">
                    <input
                      type="checkbox"
                      checked={selectedServices.includes(service.id)}
                      onChange={() => handleServiceToggle(service.id)}
                      onClick={(e) => e.stopPropagation()}
                      disabled={loading}
                    />
                  </div>
                  <div className="service-info">
                    <h4>
                      {service.icon && <span className="service-icon">{service.icon}</span>}
                      {service.name}
                    </h4>
                    <p className="service-id">ID: {service.id.slice(0, 8)}...</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="selected-count">
              {selectedServices.length} service{selectedServices.length !== 1 ? 's' : ''} selected
            </div>
          </div>
        )}

        {/* Deploy Button */}
        <div className="form-actions">
          <button
            onClick={handleDeploy}
            disabled={!isFormValid() || loading}
            className="deploy-btn"
          >
            {loading ? 'Deploying...' : 'Deploy Selected Services'}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
          <button onClick={() => setError(null)} className="alert-close">×</button>
        </div>
      )}

      {/* Success Display */}
      {success && (
        <div className="alert alert-success">
          <strong>Success:</strong> {success}
          <button onClick={() => setSuccess(null)} className="alert-close">×</button>
        </div>
      )}

      {/* Deployment Results */}
      {deployments.length > 0 && (
        <div className="deployment-results">
          <h3>Deployment Status</h3>
          <div className="deployments-list">
            {deployments.map((deployment, index) => (
              <div key={index} className="deployment-item">
                <div className="deployment-header">
                  <h4>{deployment.serviceName}</h4>
                  {deployment.deployment && (
                    <span 
                      className="deployment-status-badge"
                      style={{ backgroundColor: getStatusColor(deployment.deployment.status) }}
                    >
                      {deployment.deployment.status}
                    </span>
                  )}
                  {deployment.error && (
                    <span className="deployment-status-badge" style={{ backgroundColor: '#ef4444' }}>
                      FAILED
                    </span>
                  )}
                </div>
                
                {deployment.deployment && (
                  <div className="deployment-details">
                    <div className="deployment-info-row">
                      <span className="label">Deployment ID:</span>
                      <span className="value">{deployment.deployment.id}</span>
                    </div>
                    <div className="deployment-info-row">
                      <span className="label">Created:</span>
                      <span className="value">
                        {new Date(deployment.deployment.created_at).toLocaleString()}
                      </span>
                    </div>
                    {deployment.deployment.static_url && (
                      <div className="deployment-info-row">
                        <span className="label">URL:</span>
                        <a 
                          href={deployment.deployment.static_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="deployment-url"
                        >
                          {deployment.deployment.static_url}
                        </a>
                      </div>
                    )}
                  </div>
                )}
                
                {deployment.error && (
                  <div className="deployment-error">
                    <strong>Error:</strong> {deployment.error}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default UATDeployment;
