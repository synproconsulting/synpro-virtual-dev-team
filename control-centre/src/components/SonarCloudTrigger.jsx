import React, { useState, useEffect } from 'react';
import { triggerSonarAnalysis, fetchSonarResults } from '../api/sonarApi';
import SonarResultsView from './SonarResultsView';
import { useProduct } from '../contexts/ProductContext';
import './SonarCloudTrigger.css';

const deriveSonarKey = (creds) => {
  if (!creds) return '';
  const org = (creds.github_org || '').trim();
  const repo = (creds.github_repo || '').trim();
  if (!org && !repo) return '';
  if (!org) return repo;
  return `${org}_${repo}`;
};

const SonarCloudTrigger = () => {
  const { productCredentials, loadingCredentials, credentialsError } = useProduct();

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
  const [activeView, setActiveView] = useState('trigger');

  // Sync the SonarCloud project key with the selected product.
  useEffect(() => {
    const derived = deriveSonarKey(productCredentials);
    setSonarConfig(prev => ({ ...prev, projectKey: derived }));
    setAnalysisResults(null);
    setResult(null);
    setError(null);
  }, [productCredentials?.id, productCredentials?.github_org, productCredentials?.github_repo]);

  useEffect(() => {
    const loadInitialResults = async () => {
      if (sonarConfig.projectKey && activeView === 'results') {
        await handleFetchResults();
      }
    };
    loadInitialResults();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeView]);

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
      setTimeout(() => {
        setActiveView('results');
      }, 2000);
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
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to fetch SonarCloud results');
      setAnalysisResults(null);
    } finally {
      setFetchingResults(false);
    }
  };

  const isFormValid = () => {
    return sonarConfig.projectKey.trim() !== '';
  };

  if (loadingCredentials) {
    return <div className="sonar-trigger-container"><p>Loading product credentials…</p></div>;
  }
  if (credentialsError) {
    return <div className="sonar-trigger-container"><p>Error loading credentials: {credentialsError}</p></div>;
  }
  if (!productCredentials) {
    return <div className="sonar-trigger-container"><p>Select a product to view SonarCloud results</p></div>;
  }

  return (
    <div className="sonar-trigger-container">
      <div className="sonar-header">
        <h2>SonarCloud Analysis</h2>
        <div className="view-toggle">
          <button
            className={`toggle-btn ${activeView === 'trigger' ? 'active' : ''}`}
            onClick={() => setActiveView('trigger')}
          >
            Trigger Analysis
          </button>
          <button
            className={`toggle-btn ${activeView === 'results' ? 'active' : ''}`}
            onClick={() => setActiveView('results')}
            disabled={!sonarConfig.projectKey}
          >
            View Results
          </button>
        </div>
      </div>

      <div className="sonar-form">
        <div className="form-row">
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
        </div>

        {activeView === 'trigger' && (
          <div className="button-group">
            <button
              onClick={handleTriggerAnalysis}
              disabled={loading || !isFormValid()}
              className="btn-primary"
            >
              {loading ? 'Triggering...' : 'Trigger Analysis'}
            </button>
          </div>
        )}

        {activeView === 'results' && (
          <div className="button-group">
            <button
              onClick={handleFetchResults}
              disabled={fetchingResults || !isFormValid()}
              className="btn-secondary"
            >
              {fetchingResults ? 'Fetching...' : 'Refresh Results'}
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {activeView === 'trigger' && result && (
        <div className="alert alert-success">
          <strong>Analysis Triggered Successfully!</strong>
          {result.message && <p>{result.message}</p>}
          {result.dashboardUrl && (
            <p>
              <a href={result.dashboardUrl} target="_blank" rel="noopener noreferrer">
                View on SonarCloud →
              </a>
            </p>
          )}
        </div>
      )}

      {activeView === 'results' && (
        <>
          {fetchingResults && (
            <div className="loading-overlay">
              <div className="spinner"></div>
              <p>Loading analysis results...</p>
            </div>
          )}

          {!fetchingResults && analysisResults && (
            <SonarResultsView
              results={analysisResults}
              projectKey={sonarConfig.projectKey}
              branch={sonarConfig.branch}
            />
          )}

          {!fetchingResults && !analysisResults && !error && (
            <div className="empty-state">
              <p>No results available. Click "Refresh Results" to fetch the latest analysis.</p>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default SonarCloudTrigger;
