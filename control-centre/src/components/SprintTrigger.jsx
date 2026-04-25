import React, { useState } from 'react';
import { Play, AlertCircle, CheckCircle, Loader } from 'lucide-react';
import './SprintTrigger.css';

const SprintTrigger = ({ projectId, onTriggerSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleTriggerSprint = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/api/sprint/trigger', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ project_id: projectId }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to trigger sprint');
      }

      setSuccess(`Sprint triggered successfully! Pipeline ID: ${data.pipeline_id}`);
      if (onTriggerSuccess) {
        onTriggerSuccess(data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sprint-trigger-container">
      <div className="sprint-trigger-card">
        <h3>Sprint Trigger</h3>
        <p className="description">
          Trigger a new sprint pipeline with one click. This will initiate the CI/CD process.
        </p>

        <button
          className="trigger-button"
          onClick={handleTriggerSprint}
          disabled={loading}
        >
          {loading ? (
            <>
              <Loader className="icon spinning" />
              Triggering...
            </>
          ) : (
            <>
              <Play className="icon" />
              Trigger Sprint
            </>
          )}
        </button>

        {error && (
          <div className="message error-message">
            <AlertCircle className="icon" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="message success-message">
            <CheckCircle className="icon" />
            <span>{success}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default SprintTrigger;
