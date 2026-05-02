import React, { useState, useEffect } from 'react';
import { triggerSonarAnalysis, fetchSonarResults } from '../api/sonarApi';
import './SonarCloudTrigger.css';

const SonarCloudTrigger = () => {
  const [loading, setLoading] = useState(false);
  const [fetchingResults, setFetchingResults] = useState(false);
  const [result, setResult] = useState(null);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [sonarConfig, setSonarConfig] = useState({
    projectKey: '',
    branch: 'main',
    pullRequest: ''
  });

  // Auto-refresh results every 30 seconds if enabled
  useEffect(() => {
    let interval;
    if (autoRefresh && sonarConfig.projectKey && analysisResults) {
      interval = setInterval(() => {
        handleFetchResults(true); // silent refresh
      }, 30000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh, sonarConfig.projectKey, analysisResults]);

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

    try {
      const response = await triggerSonarAnalysis(sonarConfig);
      setResult(response);
      // After triggering, auto-fetch results
      setTimeout(() => {
        handleFetchResults();
      }, 2000);
    } catch (err) {
      setError(err.message || 'Failed to trigger SonarCloud analysis');
    } finally {
      setLoading(false);
    }
  };

  const handleFetchResults = async (silent = false) => {
    if (!sonarConfig.projectKey) {
      setError('Project key is required to fetch results');
      return;
    }

    if (!silent) {
      setFetchingResults(true);
      setError(null);
    }

    try {
      const response = await fetchSonarResults(sonarConfig.projectKey, sonarConfig.branch);
      setAnalysisResults(response);
      if (error && silent) {
        setError(null); // clear error on successful silent refresh
      }
    } catch (err) {
      if (!silent) {
        setError(err.message || 'Failed to fetch SonarCloud results');
      }
    } finally {
      if (!silent) {
        setFetchingResults(false);
      }
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

  const getSeverityColor = (count, type) => {
    if (count === 0) return '#52c41a';
    if (type === 'bugs' || type === 'vulnerabilities') {
      if (count > 10) return '#f5222d';
      if (count > 5) return '#faad14';
    }
    if (type === 'codeSmells') {
      if (count > 50) return '#f5222d';
      if (count > 20) return '#faad14';
    }
    return '#ff7a45';
  };

  const formatMetricValue = (metric) => {
    if (!metric || !metric.value) return 'N/A';
    return metric.value;
  };

  return (
    <div className="sonar-trigger-container">
      <div className="sonar-header">
        <h2>SonarCloud Code Quality Analysis</h2>
        <p className="sonar-subtitle">
          Monitor code quality, security vulnerabilities, and technical debt
        </p>
      </div>
      
      <div className="sonar-form">
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="projectKey">
              Project Key *
              <span className="field-hint">Your SonarCloud project identifier</span>
            </label>
            <input
              type="text"
              id="projectKey"
              name="projectKey"
              value={sonarConfig.projectKey}
              onChange={handleInputChange}
              placeholder="e.g., my-org_my-project"
              disabled={loading || fetchingResults}
            />
          </div>

          <div className="form-group">
            <label htmlFor="branch">
              Branch
              <span className="field-hint">Branch to analyze</span>
            </label>
            <input
              type="text"
              id="branch"
              name="branch"
              value={sonarConfig.branch}
              onChange={handleInputChange}
              placeholder="main"
              disabled={loading || fetchingResults}
            />
          </div>

          <div className="form-group">
            <label htmlFor="pullRequest">
              Pull Request
              <span className="field-hint">Optional PR number</span>
            </label>
            <input
              type="text"
              id="pullRequest"
              name="pullRequest"
              value={sonarConfig.pullRequest}
              onChange={handleInputChange}
              placeholder="e.g., 123"
              disabled={loading || fetchingResults}
            />
          </div>
        </div>

        <div className="form-actions">
          <button
            onClick={handleTriggerAnalysis}
            disabled={loading || !isFormValid()}
            className="btn-primary"
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Triggering...
              </>
            ) : (
              <>
                <span className="icon">🚀</span>
                Trigger Analysis
              </>
            )}
          </button>

          <button
            onClick={() => handleFetchResults(false)}
            disabled={fetchingResults || !isFormValid()}
            className="btn-secondary"
          >
            {fetchingResults ? (
              <>
                <span className="spinner"></span>
                Fetching...
              </>
            ) : (
              <>
                <span className="icon">📊</span>
                Fetch Results
              </>
            )}
          </button>

          {analysisResults && (
            <label className="auto-refresh-toggle">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
              <span>Auto-refresh (30s)</span>
            </label>
          )}
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          <span className="alert-icon">⚠️</span>
          <div>
            <strong>Error</strong>
            <p>{error}</p>
          </div>
        </div>
      )}

      {result && !analysisResults && (
        <div className="alert alert-info">
          <span className="alert-icon">ℹ️</span>
          <div>
            <strong>Analysis Trigger Information</strong>
            <p>{result.message}</p>
            {result.instructions && (
              <p className="code-snippet">{result.instructions}</p>
            )}
            {result.dashboardUrl && (
              <p>
                <a href={result.dashboardUrl} target="_blank" rel="noopener noreferrer">
                  View on SonarCloud →
                </a>
              </p>
            )}
          </div>
        </div>
      )}

      {analysisResults && (
        <div className="sonar-results">
          <div className="results-header">
            <h3>Analysis Results</h3>
            {autoRefresh && (
              <span className="refresh-indicator">
                <span className="pulse-dot"></span>
                Auto-refreshing
              </span>
            )}
          </div>
          
          {/* Quality Gate Status */}
          <div className="quality-gate-card">
            <div className="quality-gate-header">
              <span className="quality-gate-label">Quality Gate</span>
              <span 
                className="quality-gate-badge"
                style={{ backgroundColor: getQualityGateColor(analysisResults.qualityGateStatus) }}
              >
                {analysisResults.qualityGateStatus || 'UNKNOWN'}
              </span>
            </div>
            {analysisResults.qualityGateStatus === 'OK' || analysisResults.qualityGateStatus === 'PASSED' ? (
              <p className="quality-gate-message success">
                ✅ All quality gate conditions passed!
              </p>
            ) : (
              <p className="quality-gate-message failed">
                ❌ Quality gate failed. Review the issues below.
              </p>
            )}
          </div>

          {/* Issues Overview */}
          {analysisResults.issues && (
            <div className="issues-overview">
              <h4>Issues Overview</h4>
              <div className="issues-grid">
                <div className="issue-card bugs">
                  <div className="issue-header">
                    <span className="issue-icon">🐛</span>
                    <span className="issue-label">Bugs</span>
                  </div>
                  <div 
                    className="issue-count"
                    style={{ color: getSeverityColor(analysisResults.issues.bugs, 'bugs') }}
                  >
                    {analysisResults.issues.bugs || 0}
                  </div>
                  <div className="issue-description">
                    Code defects that should be fixed
                  </div>
                </div>

                <div className="issue-card vulnerabilities">
                  <div className="issue-header">
                    <span className="issue-icon">🔒</span>
                    <span className="issue-label">Vulnerabilities</span>
                  </div>
                  <div 
                    className="issue-count"
                    style={{ color: getSeverityColor(analysisResults.issues.vulnerabilities, 'vulnerabilities') }}
                  >
                    {analysisResults.issues.vulnerabilities || 0}
                  </div>
                  <div className="issue-description">
                    Security-related issues
                  </div>
                </div>

                <div className="issue-card code-smells">
                  <div className="issue-header">
                    <span className="issue-icon">💨</span>
                    <span className="issue-label">Code Smells</span>
                  </div>
                  <div 
                    className="issue-count"
                    style={{ color: getSeverityColor(analysisResults.issues.codeSmells, 'codeSmells') }}
                  >
                    {analysisResults.issues.codeSmells || 0}
                  </div>
                  <div className="issue-description">
                    Maintainability issues
                  </div>
                </div>

                <div className="issue-card security-hotspots">
                  <div className="issue-header">
                    <span className="issue-icon">🔥</span>
                    <span className="issue-label">Security Hotspots</span>
                  </div>
                  <div className="issue-count">
                    {analysisResults.issues.securityHotspots || 0}
                  </div>
                  <div className="issue-description">
                    Security-sensitive code to review
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Key Metrics */}
          {analysisResults.metrics && analysisResults.metrics.length > 0 && (
            <div className="metrics-section">
              <h4>Key Metrics</h4>
              <div className="metrics-grid">
                {analysisResults.metrics.map((metric, index) => (
                  <div key={index} className="metric-card">
                    <div className="metric-name">{metric.name}</div>
                    <div className="metric-value">{formatMetricValue(metric)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="results-footer">
            {analysisResults.dashboardUrl && (
              <a 
                href={analysisResults.dashboardUrl} 
                target="_blank" 
                rel="noopener noreferrer"
                className="btn-link-primary"
              >
                View Full Report on SonarCloud
                <span className="external-icon">↗</span>
              </a>
            )}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!analysisResults && !result && !error && (
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <h3>No Analysis Results Yet</h3>
          <p>Enter a project key and fetch results to see code quality metrics</p>
        </div>
      )}
    </div>
  );
};

export default SonarCloudTrigger;
