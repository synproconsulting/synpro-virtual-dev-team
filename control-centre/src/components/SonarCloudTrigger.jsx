import React, { useState } from 'react';
import { triggerSonarAnalysis, fetchSonarResults } from '../api/sonarApi';
import './SonarCloudTrigger.css';

const SonarCloudTrigger = () => {
  const [loading, setLoading] = useState(false);
  const [fetchingResults, setFetchingResults] = useState(false);
  const [result, setResult] = useState(null);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [error, setError] = useState(null);
  const [sonarConfig, setSonarConfig] = useState({
    projectKey: '',
    branch: 'main',
    pullRequest: ''
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setSonarConfig(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleTriggerAnalysis = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setAnalysisResults(null);

    try {
      const response = await triggerSonarAnalysis(sonarConfig);
      setResult(response);
    } catch (err) {
      setError(err.message || 'Failed to trigger SonarCloud analysis');
    } finally {
      setLoading(false);
    }
  };

  const handleFetchResults = async () => {
    if (!sonarConfig.projectKey) {
      setError('Project key is required to fetch results');
      return;
    }

    setFetchingResults(true);
    setError(null);

    try {
      const response = await fetchSonarResults(sonarConfig.projectKey, sonarConfig.branch);
      setAnalysisResults(response);
    } catch (err) {
      setError(err.message || 'Failed to fetch SonarCloud results');
    } finally {
      setFetchingResults(false);
    }
  };

  const isFormValid = () => {
    return sonarConfig.projectKey.trim() !== '';
  };

  const getQualityGateColor = (status) => {
    switch (status) {
      case 'OK':
      case 'PASSED':
        return '#52c41a';
      case 'ERROR':
      case 'FAILED':
        return '#f5222d';
      case 'WARN':
      case 'WARNING':
        return '#faad14';
      default:
        return '#8c8c8c';
    }
  };

  return (
    <div className="sonar-trigger-container">
      <h2>SonarCloud On-Demand Analysis</h2>
      
      <div className="sonar-form">
        <div className="form-group">
          <label htmlFor="projectKey">Project Key *</label>
          <input
            type="text"
            id="projectKey"
            name="projectKey"
            value={sonarConfig.projectKey}
            onChange={handleInputChange}
            placeholder="e.g., my-org_my-project"
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="branch">Branch</label>
          <input
            type="text"
            id="branch"
            name="branch"
            value={sonarConfig.branch}
            onChange={handleInputChange}
            placeholder="main"
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="pullRequest">Pull Request (optional)</label>
          <input
            type="text"
            id="pullRequest"
            name="pullRequest"
            value={sonarConfig.pullRequest}
            onChange={handleInputChange}
            placeholder="e.g., 123"
            disabled={loading}
          />
        </div>

        <div className="button-group">
          <button
            onClick={handleTriggerAnalysis}
            disabled={loading || !isFormValid()}
            className="btn-primary"
          >
            {loading ? 'Triggering...' : 'Trigger Analysis'}
          </button>

          <button
            onClick={handleFetchResults}
            disabled={fetchingResults || !isFormValid()}
            className="btn-secondary"
          >
            {fetchingResults ? 'Fetching...' : 'Fetch Results'}
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
          <strong>Analysis Triggered Successfully!</strong>
          {result.taskId && <p>Task ID: {result.taskId}</p>}
          {result.dashboardUrl && (
            <p>
              <a href={result.dashboardUrl} target="_blank" rel="noopener noreferrer">
                View on SonarCloud →
              </a>
            </p>
          )}
        </div>
      )}

      {analysisResults && (
        <div className="sonar-results">
          <h3>Analysis Results</h3>
          
          <div className="quality-gate">
            <div className="quality-gate-status">
              <span className="label">Quality Gate:</span>
              <span 
                className="status-badge"
                style={{ backgroundColor: getQualityGateColor(analysisResults.qualityGateStatus) }}
              >
                {analysisResults.qualityGateStatus || 'UNKNOWN'}
              </span>
            </div>
          </div>

          <div className="metrics-grid">
            {analysisResults.metrics && analysisResults.metrics.map((metric, index) => (
              <div key={index} className="metric-card">
                <div className="metric-name">{metric.name}</div>
                <div className="metric-value">{metric.value}</div>
              </div>
            ))}
          </div>

          {analysisResults.issues && (
            <div className="issues-summary">
              <h4>Issues Summary</h4>
              <div className="issues-grid">
                <div className="issue-type">
                  <span className="issue-label bug">Bugs</span>
                  <span className="issue-count">{analysisResults.issues.bugs || 0}</span>
                </div>
                <div className="issue-type">
                  <span className="issue-label vulnerability">Vulnerabilities</span>
                  <span className="issue-count">{analysisResults.issues.vulnerabilities || 0}</span>
                </div>
                <div className="issue-type">
                  <span className="issue-label code-smell">Code Smells</span>
                  <span className="issue-count">{analysisResults.issues.codeSmells || 0}</span>
                </div>
              </div>
            </div>
          )}

          {analysisResults.dashboardUrl && (
            <div className="dashboard-link">
              <a href={analysisResults.dashboardUrl} target="_blank" rel="noopener noreferrer">
                View Full Report on SonarCloud →
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SonarCloudTrigger;