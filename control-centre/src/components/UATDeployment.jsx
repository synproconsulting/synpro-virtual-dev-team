import React, { useState, useEffect } from 'react';
import {
  listServices,
  listEnvironments,
  triggerDeployment,
  getDeploymentHistory,
  pollDeploymentStatus,
} from '../api/railway';
import './UATDeployment.css';

const UATDeployment = () => {
  const [loading, setLoading] = useState(false);
  const [loadingServices, setLoadingServices] = useState(true);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [selectedServices, setSelectedServices] = useState([]);
  const [availableServices, setAvailableServices] = useState([]);
  const [availableEnvironments, setAvailableEnvironments] = useState([]);
  const [selectedEnvironment, setSelectedEnvironment] = useState(null);
  const [deploymentNotes, setDeploymentNotes] = useState('');
  const [deploymentHistory, setDeploymentHistory] = useState([]);
  const [pollingDeployments, setPollingDeployments] = useState(new Set());

  // Load services and environments on mount
  useEffect(() => {
    loadServicesAndEnvironments();
    loadDeploymentHistory();
  }, []);

  const loadServicesAndEnvironments = async () => {
    setLoadingServices(true);
    setError(null);
    
    try {
      const [services, environments] = await Promise.all([
        listServices(),
        listEnvironments(),
      ]);
      
      setAvailableServices(services);
      setAvailableEnvironments(environments);
      
      // Auto-select UAT environment if available
      const uatEnv = environments.find(env => 
        env.name.toLowerCase() === 'uat' || 
        env.name.toLowerCase() === 'staging'
      );
      if (uatEnv) {
        setSelectedEnvironment(uatEnv.id);
      }
    } catch (err) {
      console.error('Failed to load services and environments:', err);
      setError(`Failed to load Railway data: ${err.message}`);
    } finally {
      setLoadingServices(false);
    }
  };

  const loadDeploymentHistory = async () => {
    try {
      const history = await getDeploymentHistory({ limit: 5 });
      setDeploymentHistory(history.deployments || []);
    } catch (err) {
      console.error('Failed to load deployment history:', err);
      // Don't show error for history - it's not critical
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
    if (selectedServices.length === availableServices.length) {
      setSelectedServices([]);
    } else {
      setSelectedServices(availableServices.map(s => s.id));
    }
  };

  const startPolling = async (deploymentId) => {
    setPollingDeployments(prev => new Set([...prev, deploymentId]));
    
    try {
      await pollDeploymentStatus(
        deploymentId,
        (status) => {
          // Update the deployment in history
          setDeploymentHistory(prev => {
            const index = prev.findIndex(d => d.id === deploymentId);
            if (index !== -1) {
              const updated = [...prev];
              updated[index] = status;
              return updated;
            }
            return prev;
          });
        },
        5000, // Poll every 5 seconds
        600000 // 10 minute timeout
      );
    } catch (err) {
      console.error(`Polling failed for deployment ${deploymentId}:`, err);
    } finally {
      setPollingDeployments(prev => {
        const updated = new Set(prev);
        updated.delete(deploymentId);
        return updated;
      });
    }
  };

  const handleTriggerDeployment = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload = {
        service_ids: selectedServices,
        environment_id: selectedEnvironment,
        deployment_notes: deploymentNotes || undefined,
      };
      
      const response = await triggerDeployment(payload);
      setResult(response);
      
      // Start polling for each deployment
      if (response.deployments) {
        response.deployments.forEach(deployment => {
          startPolling(deployment.id);
        });
      }
      
      // Refresh deployment history
      await loadDeploymentHistory();
      
      // Clear selection
      setSelectedServices([]);
      setDeploymentNotes('');
    } catch (err) {
      setError(err.message || 'Failed to trigger UAT deployment');
    } finally {
      setLoading(false);
    }
  };

  const isFormValid = () => {
    return selectedServices.length > 0 && selectedEnvironment;
  };

  const getStatusBadgeClass = (status) => {
    const statusLower = status.toLowerCase();
    if (statusLower === 'success' || statusLower === 'active') return 'status-success';
    if (statusLower === 'failed' || statusLower === 'crashed') return 'status-error';
    if (statusLower === 'building' || statusLower === 'deploying') return 'status-progress';
    return 'status-pending';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleString();
    } catch {
      return dateString;
    }
  };

  if (loadingServices) {
    return (
      <div className="uat-deployment-container">
        <div className="uat-deployment-header">
          <h2>UAT Deployment</h2>
          <p className="subtitle">Loading Railway services...</p>
        </div>
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="uat-deployment-container">
      <div className="uat-deployment-header">
        <h2>UAT Deployment</h2>
        <p className="subtitle">Deploy services to Railway UAT environment</p>
      </div>

      <div className="uat-deployment-form">
        <div className="form-section">
          <h3>Deployment Configuration</h3>
          
          {availableEnvironments.length > 0 && (
            <div className="form-group">
              <label htmlFor="environment">Environment</label>
              <select
                id="environment"
                value={selectedEnvironment || ''}
                onChange={(e) => setSelectedEnvironment(e.target.value)}
              >
                <option value="">Select Environment</option>
                {availableEnvironments.map(env => (
                  <option key={env.id} value={env.id}>
                    {env.name}
                  </option>
                ))}
              </select>
            </div>
          )}

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
            <h3>Select Services to Deploy</h3>
            <button
              type="button"
              onClick={handleSelectAll}
              className="select-all-btn"
            >
              {selectedServices.length === availableServices.length ? 'Deselect All' : 'Select All'}
            </button>
          </div>

          {availableServices.length === 0 ? (
            <div className="alert alert-warning">
              <p>No services found in Railway project. Please check your Railway configuration.</p>
            </div>
          ) : (
            <>
              <div className="services-grid">
                {availableServices.map(service => (
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
                      {service.icon && <span className="service-icon">{service.icon}</span>}
                      <h4>{service.name}</h4>
                      <p className="service-id">{service.id}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="selected-count">
                {selectedServices.length} service{selectedServices.length !== 1 ? 's' : ''} selected
              </div>
            </>
          )}
        </div>

        <div className="form-actions">
          <button
            onClick={handleTriggerDeployment}
            disabled={!isFormValid() || loading}
            className="deploy-btn"
          >
            {loading ? 'Deploying...' : 'Deploy to UAT'}
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className={`alert ${result.success ? 'alert-success' : 'alert-warning'}`}>
          <h3>{result.message}</h3>
          
          {result.deployments && result.deployments.length > 0 && (
            <div className="result-details">
              <h4>Triggered Deployments:</h4>
              <ul>
                {result.deployments.map(deployment => (
                  <li key={deployment.id}>
                    <strong>{deployment.service_name}</strong> - {deployment.status}
                    {deployment.url && (
                      <span>
                        {' '}(<a href={deployment.url} target="_blank" rel="noopener noreferrer">
                          View Service
                        </a>)
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {result.failed_services && result.failed_services.length > 0 && (
            <div className="result-details">
              <h4>Failed Services:</h4>
              <ul>
                {result.failed_services.map((failure, idx) => (
                  <li key={idx}>
                    <strong>{failure.service_id}</strong>: {failure.error}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {deploymentHistory.length > 0 && (
        <div className="deployment-history">
          <h3>Recent Deployments</h3>
          <div className="history-list">
            {deploymentHistory.map(deployment => (
              <div key={deployment.id} className="history-item">
                <div className="history-header">
                  <div className="history-info">
                    <strong>{deployment.service_name}</strong>
                    <span className="history-env">{deployment.environment_name}</span>
                  </div>
                  <span className={`status-badge ${getStatusBadgeClass(deployment.status)}`}>
                    {deployment.status}
                    {pollingDeployments.has(deployment.id) && ' 🔄'}
                  </span>
                </div>
                <div className="history-meta">
                  <span>{formatDate(deployment.created_at)}</span>
                  {deployment.url && (
                    <a href={deployment.url} target="_blank" rel="noopener noreferrer">
                      View Service →
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
          <button 
            onClick={loadDeploymentHistory} 
            className="refresh-btn"
          >
            Refresh History
          </button>
        </div>
      )}
    </div>
  );
};

export default UATDeployment;
