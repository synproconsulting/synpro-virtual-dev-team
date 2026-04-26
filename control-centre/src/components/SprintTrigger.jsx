import React, { useState } from 'react';
import { triggerSprint } from '../api/sprintApi';
import './SprintTrigger.css';

const SprintTrigger = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [sprintConfig, setSprintConfig] = useState({
    sprintNumber: '',
    startDate: '',
    endDate: '',
    goals: '',
    team: 'default'
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setSprintConfig(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleTriggerSprint = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await triggerSprint(sprintConfig);
      setResult(response);
    } catch (err) {
      setError(err.message || 'Failed to trigger sprint');
    } finally {
      setLoading(false);
    }
  };

  const isFormValid = () => {
    return sprintConfig.sprintNumber && 
           sprintConfig.startDate && 
           sprintConfig.endDate;
  };

  return (
    <div className="sprint-trigger-container">
      <h2>One-Click Sprint Trigger</h2>
      
      <div className="sprint-form">
        <div className="form-group">
          <label htmlFor="sprintNumber">Sprint Number *</label>
          <input
            type="text"
            id="sprintNumber"
            name="sprintNumber"
            value={sprintConfig.sprintNumber}
            onChange={handleInputChange}
            placeholder="e.g., Sprint 29"
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="startDate">Start Date *</label>
          <input
            type="date"
            id="startDate"
            name="startDate"
            value={sprintConfig.startDate}
            onChange={handleInputChange}
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="endDate">End Date *</label>
          <input
            type="date"
            id="endDate"
            name="endDate"
            value={sprintConfig.endDate}
            onChange={handleInputChange}
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="goals">Sprint Goals</label>
          <textarea
            id="goals"
            name="goals"
            value={sprintConfig.goals}
            onChange={handleInputChange}
            placeholder="Enter sprint goals (optional)"
            rows="4"
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="team">Team</label>
          <select
            id="team"
            name="team"
            value={sprintConfig.team}
            onChange={handleInputChange}
            disabled={loading}
          >
            <option value="default">Default Team</option>
            <option value="backend">Backend Team</option>
            <option value="frontend">Frontend Team</option>
            <option value="fullstack">Full Stack Team</option>
          </select>
        </div>

        <button
          className="trigger-button"
          onClick={handleTriggerSprint}
          disabled={!isFormValid() || loading}
        >
          {loading ? 'Triggering Sprint...' : 'Trigger Sprint'}
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className="alert alert-success">
          <strong>Success!</strong> Sprint triggered successfully.
          <div className="result-details">
            <p>Sprint ID: {result.sprintId}</p>
            <p>Status: {result.status}</p>
            {result.jiraUrl && (
              <a href={result.jiraUrl} target="_blank" rel="noopener noreferrer">
                View in Jira
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SprintTrigger;
