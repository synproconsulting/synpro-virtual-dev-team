import React, { useState, useEffect } from 'react';
import './ManualUATDeployment.css';

const ManualUATDeployment = () => {
  const [services, setServices] = useState([]);
  const [selectedServices, setSelectedServices] = useState([]);
  const [branch, setBranch] = useState('main');
  const [deploying, setDeploying] = useState(false);
  const [deploymentStatus, setDeploymentStatus] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchServices();
  }, []);

  const fetchServices = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/uat/services');
      if (!response.ok) throw new Error('Failed to fetch services');
      const data = await response.json();
      setServices(data.services || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleServiceToggle = (serviceName) => {
    setSelectedServices(prev =>
      prev.includes(serviceName)
        ? prev.filter(s => s !== serviceName)
        : [...prev, serviceName]
    );
  };

  const handleSelectAll = () => {
    if (selectedServices.length === services.length) {
      setSelectedServices([]);
    } else {
      setSelectedServices(services.map(s => s.name));
    }
  };

  const handleDeploy = async () => {
    if (selectedServices.length === 0) {
      setError('Please select at least one service');
      return;
    }

    try {
      setDeploying(true);
      setError(null);
      setDeploymentStatus(null);

      const response = await fetch('/api/uat/deploy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          services: selectedServices,
          branch: branch,
          environment: 'uat'
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Deployment failed');
      }

      const data = await response.json();
      setDeploymentStatus({
        success: true,
        deploymentId: data.deployment_id,
        message: data.message
      });
      setSelectedServices([]);
    } catch (err) {
      setError(err.message);
      setDeploymentStatus({ success: false });
    } finally {
      setDeploying(false);
    }
  };

  if (loading) {
    return <div className="uat-deployment-loading">Loading services...</div>;
  }

  return (
    <div className="uat-deployment-container">
      <div className="uat-deployment-header">
        <h2>Manual UAT Deployment</h2>
        <p className="uat-deployment-subtitle">
          Select services to deploy to UAT environment
        </p>
      </div>

      {error && (
        <div className="uat-deployment-alert uat-deployment-alert-error">
          <span className="alert-icon">⚠️</span>
          {error}
        </div>
      )}

      {deploymentStatus && deploymentStatus.success && (
        <div className="uat-deployment-alert uat-deployment-alert-success">
          <span className="alert-icon">✓</span>
          {deploymentStatus.message}
          {deploymentStatus.deploymentId && (
            <div className="deployment-id">
              Deployment ID: {deploymentStatus.deploymentId}
            </div>
          )}
        </div>
      )}

      <div className="uat-deployment-controls">
        <div className="branch-selector">
          <label htmlFor="branch-input">Branch:</label>
          <input
            id="branch-input"
            type="text"
            value={branch}
            onChange={(e) => setBranch(e.target.value)}
            placeholder="main"
            disabled={deploying}
          />
        </div>

        <button
          className="select-all-btn"
          onClick={handleSelectAll}
          disabled={deploying || services.length === 0}
        >
          {selectedServices.length === services.length ? 'Deselect All' : 'Select All'}
        </button>
      </div>

      <div className="service-list">
        {services.length === 0 ? (
          <div className="no-services">No services available</div>
        ) : (
          services.map((service) => (
            <div key={service.name} className="service-item">
              <label className="service-checkbox">
                <input
                  type="checkbox"
                  checked={selectedServices.includes(service.name)}
                  onChange={() => handleServiceToggle(service.name)}
                  disabled={deploying}
                />
                <span className="service-name">{service.name}</span>
              </label>
              <div className="service-info">
                <span className="service-version">
                  {service.current_version || 'N/A'}
                </span>
                {service.status && (
                  <span className={`service-status status-${service.status}`}>
                    {service.status}
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      <div className="uat-deployment-actions">
        <button
          className="deploy-btn"
          onClick={handleDeploy}
          disabled={deploying || selectedServices.length === 0}
        >
          {deploying ? (
            <>
              <span className="spinner"></span>
              Deploying...
            </>
          ) : (
            `Deploy ${selectedServices.length} service${selectedServices.length !== 1 ? 's' : ''}`
          )}
        </button>
      </div>
    </div>
  );
};

export default ManualUATDeployment;
