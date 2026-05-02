import React, { useState, useEffect } from 'react';
import {
  getServices,
  getEnvironments,
  triggerDeployment,
  getDeploymentStatus,
  getServiceDeployments,
} from '../api/deploymentApi';
import './UATDeployment.css';

const UATDeployment = () => {
  const [loading, setLoading] = useState(false);
  const [servicesLoading, setServicesLoading] = useState(true);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [services, setServices] = useState([]);
  const [environments, setEnvironments] = useState([]);
  const [selectedServices, setSelectedServices] = useState([]);
  const [selectedEnvironment, setSelectedEnvironment] = useState(null);
  const [customBranch, setCustomBranch] = useState('');
  const [deploymentNotes, setDeploymentNotes] = useState('');
  const [recentDeployments, setRecentDeployments] = useState({});
  const [pollingDeployments, setPollingDeployments] = useState(new Set());

  // Load services and environments on mount
  useEffect(() => {
    loadServicesAndEnvironments();
  }, []);

  // Poll deployment status for active deployments
  useEffect(() => {
    if (pollingDeployments.size === 0) return;

    const interval = setInterval(() => {
      pollingDeployments.forEach(async (deploymentId) => {
        try {
          const statusData = await getDeploymentStatus(deploymentId);
          const status = statusData.deployment?.status;
          
          // Stop polling if deployment is complete or failed
          if (status === 'SUCCESS' || status === 'FAILED' || status === 'CRASHED') {
            setPollingDeployments(prev => {
              const next = new Set(prev);
              next.delete(deploymentId);
              return next;
            });
          }
        } catch (err) {
          console.error('Error polling deployment status:', err);
        }
      });
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(interval);
  }, [pollingDeployments]);

  const loadServicesAndEnvironments = async () => {
    setServicesLoading(true);
    setError(null);
    
    try {
      const [servicesData, environmentsData] = await Promise.all([
        getServices(),
        getEnvironments(),
      ]);
      
      setServices(servicesData.services || []);
      setEnvironments(environmentsData.environments || []);
      
      // Auto-select UAT environment if available
      const uatEnv = environmentsData.environments?.find(
        env => env.name.toLowerCase() === 'uat'
      );
      if (uatEnv) {
        setSelectedEnvironment(uatEnv.id);
      } else if (environmentsData.environments?.length > 0) {
        setSelectedEnvironment(environmentsData.environments[0].id);
      }
    } catch (err) {
      setError(err.message || 'Failed to load services and environments');
    } finally {
      setServicesLoading(false);
    }
  };

  const loadServiceDeployments = async (serviceId) => {
    try {
      const deploymentsData = await getServiceDeployments(serviceId, 5);
      setRecentDeployments(prev => ({
        ...prev,
        [serviceId]: deploymentsData.deployments || [],
      }));
    } catch (err) {
      console.error('Error loading service deployments:', err);
    }
  };

  const handleServiceToggle = (serviceId) => {
    setSelectedServices(prev => {
      if (prev.includes(serviceId)) {
        return prev.filter(id => id !== serviceId);
      } else {
        // Load recent deployments when service is selected
        loadServiceDeployments(serviceId);
        return [...prev, serviceId];
      }
    });
  };

  const handleSelectAll = () => {
    if (selectedServices.length === services.length) {
      setSelectedServices([]);
      setRecentDeployments({});
    } else {
      const allServiceIds = services.map(s => s.id);
      setSelectedServices(allServiceIds);
      // Load deployments for all services
      allServiceIds.forEach(loadServiceDeployments);
    }
  };

  const handleTriggerDeployment = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Trigger deployment for each selected service
      const deploymentPromises = selectedServices.map(serviceId =>
        triggerDeployment(
          serviceId,
          selectedEnvironment,
          customBranch || null,
          deploymentNotes || null
        )
      );

      const results = await Promise.all(deploymentPromises);
      
      // Start polling for these deployments
      const newDeploymentIds = results.map(r => r.deployment_id);
      setPollingDeployments(prev => new Set([...prev, ...newDeploymentIds]));

      setResult({
        success: true,
        deployments: results,
        count: results.length,
      });

      // Refresh deployment lists
      selectedServices.forEach(loadServiceDeployments);

    } catch (err) {
      setError(err.message || 'Failed to trigger deployments');
    } finally {
      setLoading(false);
    }
  };

  const isFormValid = () => {
    return selectedServices.length > 0 && selectedEnvironment;
  };

  const getStatusBadgeClass = (status) => {
    const statusLower = status?.toLowerCase() || '';
    if (statusLower === 'success') return 'status-success';
    if (statusLower === 'building' || statusLower === 'deploying') return 'status-building';
    if (statusLower === 'failed' || statusLower === 'crashed') return 'status-failed';
    return 'status-unknown';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <div className="uat-deployment-container">
      <div className="uat-deployment-header">
        <h2>UAT Deployment - Railway</h2>
        <p className="subtitle">Deploy selected services to Railway UAT environment</p>
      </div>

      {servicesLoading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading services from Railway...</p>
        </div>
      ) : (
        <>
          <div className="uat-deployment-form">
            <div className="form-section">
              <h3>Deployment Configuration</h3>
              
              <div className="form-group">
                <label htmlFor="environment">Environment</label>
                <select
                  id="environment"
                  value={selectedEnvironment || ''}
                  onChange={(e) => setSelectedEnvironment(e.target.value)}
                >
                  {environments.map(env => (
                    <option key={env.id} value={env.id}>
                      {env.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="customBranch">Custom Branch (Optional)</label>
                <input
                  type="text"
                  id="customBranch"
                  value={customBranch}
                  onChange={(e) => setCustomBranch(e.target.value)}
                  placeholder="e.g., feature/new-feature (leave empty for default)"
                />
                <small>Leave empty to use the default branch configured in Railway</small>
              </div>

              <div className="form-group">
                <label htmlFor="deploymentNotes">Deployment Notes (Optional)</label>
                <textarea
                  id="deploymentNotes"
                  value={deploymentNotes}
                  onChange={(e) => setDeploymentNotes(e.target.value)}
                  placeholder="Enter any notes about this deployment..."
                  rows="3"
                />
              </div>
            </div>

            <div className="form-section">
              <div className="services-header">
                <h3>Select Services to Deploy ({services.length} available)</h3>
                <button
                  type="button"
                  onClick={handleSelectAll}
                  className="select-all-btn"
                  disabled={services.length === 0}
                >
                  {selectedServices.length === services.length ? 'Deselect All' : 'Select All'}
                </button>
              </div>

              {services.length === 0 ? (
                <div className="empty-state">
                  <p>No services found in Railway project</p>
                </div>
              ) : (
                <div className="services-grid">
                  {services.map(service => (
                    <div
                      key={service.id}
                      className={`service-card ${
                        selectedServices.includes(service.id) ? 'selected' : ''
                      }`}
                      onClick={() => handleServiceToggle(service.id)}
                    >
                      <div className="service-checkbox">
                        <input
                          type="checkbox"
                          checked={selectedServices.includes(service.id)}
                          onChange={() => handleServiceToggle(service.id)}
                          onClick={(e) => e.stopPropagation()}
                        />
                      </div>
                      <div className="service-info">
                        <h4>{service.name}</h4>
                        <small>ID: {service.id.substring(0, 8)}...</small>
                        
                        {/* Show recent deployments for selected services */}
                        {selectedServices.includes(service.id) && recentDeployments[service.id] && (
                          <div className="recent-deployments">
                            <p className="recent-title">Recent Deployments:</p>
                            {recentDeployments[service.id].slice(0, 3).map(dep => (
                              <div key={dep.id} className="deployment-mini">
                                <span className={`status-badge ${getStatusBadgeClass(dep.status)}`}>
                                  {dep.status}
                                </span>
                                <span className="deployment-time">
                                  {formatDate(dep.created_at)}
                                </span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="selected-count">
                {selectedServices.length} service{selectedServices.length !== 1 ? 's' : ''} selected
              </div>
            </div>

            <div className="form-actions">
              <button
                onClick={handleTriggerDeployment}
                disabled={!isFormValid() || loading}
                className="deploy-btn"
              >
                {loading ? 'Deploying...' : `Deploy ${selectedServices.length} Service${selectedServices.length !== 1 ? 's' : ''}`}
              </button>
            </div>
          </div>

          {error && (
            <div className="alert alert-error">
              <strong>Error:</strong> {error}
            </div>
          )}

          {result && result.success && (
            <div className="alert alert-success">
              <h3>Deployment Triggered Successfully</h3>
              <div className="result-details">
                <p><strong>Services Deployed:</strong> {result.count}</p>
                <div className="deployments-list">
                  {result.deployments.map((dep, idx) => (
                    <div key={idx} className="deployment-result">
                      <p><strong>Deployment ID:</strong> {dep.deployment_id}</p>
                      <p><strong>Status:</strong> <span className={`status-badge ${getStatusBadgeClass(dep.status)}`}>{dep.status}</span></p>
                      <p><strong>Triggered:</strong> {formatDate(dep.triggered_at)}</p>
                      {dep.static_url && (
                        <p>
                          <strong>URL:</strong>{' '}
                          <a href={dep.static_url} target="_blank" rel="noopener noreferrer">
                            {dep.static_url}
                          </a>
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {pollingDeployments.size > 0 && (
            <div className="alert alert-info">
              <p>Monitoring {pollingDeployments.size} active deployment{pollingDeployments.size !== 1 ? 's' : ''}...</p>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default UATDeployment;
