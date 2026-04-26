import React, { useState } from 'react';
import { triggerSprint } from '../api/sprintApi';
import './SprintTrigger.css';

const SprintTrigger = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [sprintName, setSprintName] = useState('');
  const [duration, setDuration] = useState(2);

  const handleTrigger = async () => {
    if (!sprintName.trim()) {
      setError('Sprint name is required');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await triggerSprint({
        name: sprintName,
        duration_weeks: duration
      });
      setSuccess(`Sprint "${result.name}" triggered successfully! ID: ${result.sprint_id}`);
      setSprintName('');
    } catch (err) {
      setError(err.message || 'Failed to trigger sprint');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sprint-trigger-container">
      <h2>One-Click Sprint Trigger</h2>
      
      <div className="sprint-form">
        <div className="form-group">
          <label htmlFor="sprintName">Sprint Name:</label>
          <input
            id="sprintName"
            type="text"
            value={sprintName}
            onChange={(e) => setSprintName(e.target.value)}
            placeholder="e.g., Sprint 42"
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="duration">Duration (weeks):</label>
          <select
            id="duration"
            value={duration}
            onChange={(e) => setDuration(parseInt(e.target.value))}
            disabled={loading}
          >
            <option value="1">1 week</option>
            <option value="2">2 weeks</option>
            <option value="3">3 weeks</option>
            <option value="4">4 weeks</option>
          </select>
        </div>

        <button
          className="trigger-button"
          onClick={handleTrigger}
          disabled={loading}
        >
          {loading ? 'Triggering...' : 'Trigger Sprint'}
        </button>
      </div>

      {error && <div className="message error-message">{error}</div>}
      {success && <div className="message success-message">{success}</div>}
    </div>
  );
};

export default SprintTrigger;
