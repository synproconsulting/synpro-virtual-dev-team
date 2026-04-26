import React, { useState } from 'react';
import { triggerUATDeployment } from '../api/deploymentApi';
import './UATDeployment.css';

const UATDeployment = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [deploymentConfig, setDeploymentConfig] = useState({
    environment: 'uat',
    branch: 'develop',
    deploymentNotes: ''
  });
  const [selectedServices, setSelectedServices] = useState([]);

  const availableServices = [
    { id: 'api-gateway', name: 'API Gateway', description: 'Main API service' },
    { id: 'auth-service', name: 'Auth Service', description: 'Authentication and authorization' },
    { id: 'user-service', name: 'User Service', description: 'User management' },
    { id: 'notification-service', name: 'Notification Service', description: 'Email and SMS notifications' },
    { id: 'analytics-service', name: 'Analytics Service', description: 'Data analytics and reporting' },
    { id: 'payment-service', name: 'Payment Service', description: 'Payment processing' },
    { id: 'frontend-app', name: 'Frontend Application', description: 'React web application' }
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setDeploymentConfig(prev => ({
      ...prev,
      [name]: value
    }));
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

  const handleTriggerDeployment = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload = {
        ...deploymentConfig,
        services: selectedServices
      };
      const response = await triggerUATDeployment(payload);
      setResult(response);
    } catch (err) {
      setError(err.message || 'Failed to trigger UAT deployment');
    } finally {
      setLoading(false);
    }
  };

  const isFormValid = () => {
    return deploymentConfig.branch && selectedServices.length > 0;
  };

  return (
    <div className="uat-deployment-container">
      <div className="uat-deployment-header">
        <h2>Manual UAT Deployment</h2>
        <p className="subtitle">Deploy selected services to UAT environment</p>
      </div>

      <div className="uat-deployment-form">
        <div className="form-section">
          <h3>Deployment Configuration</h3>
          <div className="form-group">
            <label htmlFor="environment">Environment</label>
            <select
              id="environment"
              name="environment"
              value={deploymentConfig.environment}
              onChange={handleInputChange}
              disabled
            >
              <option value="uat">UAT</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="branch">Branch</label>
            <input
              type="text"
              id="branch"
              name="branch"
              value={deploymentConfig.branch}
              onChange={handleInputChange}
              placeholder="e.g., develop, feature/new-feature"
            />
          </div>

          <div className="form-group">
            <label htmlFor="deploymentNotes">Deployment Notes (Optional)</label>
            <textarea
              id="deploymentNotes"
              name="deploymentNotes"
              value={deploymentConfig.deploymentNotes}
              onChange={handleInputChange}
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
                  <h4>{service.name}</h4>
                  <p>{service.description}</p>
                </div>
              </div>
            ))}
          </div>

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
        <div className="alert alert-success">
          <h3>Deployment Triggered Successfully</h3>
          <div className="result-details">
            <p><strong>Deployment ID:</strong> {result.deploymentId}</p>
            <p><strong>Status:</strong> {result.status}</p>
            {result.pipelineUrl && (
              <p>
                <strong>Pipeline:</strong>{' '}
                <a href={result.pipelineUrl} target="_blank" rel="noopener noreferrer">
                  View Pipeline
                </a>
              </p>
            )}
            {result.estimatedDuration && (
              <p><strong>Estimated Duration:</strong> {result.estimatedDuration}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default UATDeployment;