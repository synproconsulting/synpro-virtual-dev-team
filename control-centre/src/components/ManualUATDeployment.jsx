import React, { useState, useEffect } from 'react';
import './ManualUATDeployment.css';

const ManualUATDeployment = () => {
  const [services, setServices] = useState([]);
  const [selectedServices, setSelectedServices] = useState([]);
  const [deploymentStatus, setDeploymentStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [deploymentHistory, setDeploymentHistory] = useState([]);

  useEffect(() => {
    fetchAvailableServices();
    fetchDeploymentHistory();
  }, []);

  const fetchAvailableServices = async () => {
    try {
      const response = await fetch('/api/uat/services');
      if (!response.ok) throw new Error('Failed to fetch services');
      const data = await response.json();
      setServices(data.services || []);
    } catch (err) {
      setError(`Error loading services: ${err.message}`);
    }
  };

  const fetchDeploymentHistory = async () => {
    try {
      const response = await fetch('/api/uat/deployments/history');
      if (!response.ok) throw new Error('Failed to fetch history');
      const data = await response.json();
      setDeploymentHistory(data.deployments || []);
    } catch (err) {
      console.error('Error loading deployment history:', err);
    }
  };

  const handleServiceToggle = (serviceId) => {
    setSelectedServices(prev => 
      prev.includes(serviceId)
        ? prev.filter(id => id !== serviceId)
        : [...prev, serviceId]
    );
  };

  const handleSelectAll = () => {
    if (selectedServices.length === services.length) {
      setSelectedServices([]);
    } else {
      setSelectedServices(services.map(s => s.id));
    }
  };

  const handleDeploy = async () => {
    if (selectedServices.length === 0) {
      setError('Please select at least one service to deploy');
      return;
    }

    setLoading(true);
    setError(null);
    setDeploymentStatus(null);

    try {
      const response = await fetch('/api/uat/deploy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service_ids: selectedServices })
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Deployment failed');
      }

      setDeploymentStatus({
        success: true,
        message: data.message,
        deployment_id: data.deployment_id
      });
      
      setSelectedServices([]);
      fetchDeploymentHistory();
    } catch (err) {
      setError(`Deployment failed: ${err.message}`);
      setDeploymentStatus({ success: false });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="manual-uat-deployment">
      <div className="deployment-header">
        <h2>Manual UAT Deployment</h2>
        <p className="subtitle">Select services to deploy to UAT environment</p>
      </div>

      {error && (
        <div className="alert alert-error">
          <span className="alert-icon">⚠️</span>
          {error}
        </div>
      )}

      {deploymentStatus?.success && (
        <div className="alert alert-success">
          <span className="alert-icon">✓</span>
          {deploymentStatus.message}
          {deploymentStatus.deployment_id && (
            <span className="deployment-id"> (ID: {deploymentStatus.deployment_id})</span>
          )}
        </div>
      )}

      <div className="deployment-grid">
        <div className="services-panel">
          <div className="panel-header">
            <h3>Available Services</h3>
            <button 
              className="btn-link" 
              onClick={handleSelectAll}
              disabled={loading}
            >
              {selectedServices.length === services.length ? 'Deselect All' : 'Select All'}
            </button>
          </div>

          <div className="services-list">
            {services.map(service => (
              <div 
                key={service.id} 
                className={`service-item ${selectedServices.includes(service.id) ? 'selected' : ''}`}
                onClick={() => !loading && handleServiceToggle(service.id)}
              >
                <input 
                  type="checkbox" 
                  checked={selectedServices.includes(service.id)}
                  onChange={() => handleServiceToggle(service.id)}
                  disabled={loading}
                />
                <div className="service-info">
                  <span className="service-name">{service.name}</span>
                  <span className="service-version">v{service.version}</span>
                </div>
                <span className={`service-status status-${service.status}`}>
                  {service.status}
                </span>
              </div>
            ))}
          </div>

          <div className="panel-footer">
            <div className="selection-summary">
              {selectedServices.length} of {services.length} services selected
            </div>
            <button 
              className="btn-primary btn-deploy"
              onClick={handleDeploy}
              disabled={loading || selectedServices.length === 0}
            >
              {loading ? 'Deploying...' : 'Deploy to UAT'}
            </button>
          </div>
        </div>

        <div className="history-panel">
          <h3>Recent Deployments</h3>
          <div className="history-list">
            {deploymentHistory.length === 0 ? (
              <div className="empty-state">No deployment history</div>
            ) : (
              deploymentHistory.slice(0, 10).map(deployment => (
                <div key={deployment.id} className="history-item">
                  <div className="history-header">
                    <span className={`status-badge status-${deployment.status}`}>
                      {deployment.status}
                    </span>
                    <span className="history-time">{deployment.timestamp}</span>
                  </div>
                  <div className="history-services">
                    {deployment.services.join(', ')}
                  </div>
                  <div className="history-user">by {deployment.user}</div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ManualUATDeployment;