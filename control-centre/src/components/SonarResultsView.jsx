import React, { useState, useEffect } from 'react';
import { fetchSonarIssues } from '../api/sonarApi';
import './SonarResultsView.css';

const SonarResultsView = ({ results, projectKey, branch }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [issues, setIssues] = useState([]);
  const [loadingIssues, setLoadingIssues] = useState(false);
  const [issueFilters, setIssueFilters] = useState({
    types: '',
    severities: '',
    statuses: 'OPEN,CONFIRMED,REOPENED'
  });

  useEffect(() => {
    if (activeTab === 'issues') {
      loadIssues();
    }
  }, [activeTab, issueFilters]);

  const loadIssues = async () => {
    setLoadingIssues(true);
    try {
      const issuesData = await fetchSonarIssues(projectKey, branch, issueFilters);
      setIssues(issuesData);
    } catch (error) {
      console.error('Failed to load issues:', error);
      setIssues([]);
    } finally {
      setLoadingIssues(false);
    }
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

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'BLOCKER':
        return '#f5222d';
      case 'CRITICAL':
        return '#ff4d4f';
      case 'MAJOR':
        return '#fa8c16';
      case 'MINOR':
        return '#faad14';
      case 'INFO':
        return '#1890ff';
      default:
        return '#8c8c8c';
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'BUG':
        return '🐛';
      case 'VULNERABILITY':
        return '🔒';
      case 'CODE_SMELL':
        return '👃';
      case 'SECURITY_HOTSPOT':
        return '🔥';
      default:
        return '📋';
    }
  };

  const formatMetricValue = (value, metric) => {
    if (!value) return 'N/A';
    
    // Handle percentages
    if (metric.includes('coverage') || metric.includes('density') || metric.includes('duplicated')) {
      return `${parseFloat(value).toFixed(1)}%`;
    }
    
    // Handle ratings (A-E)
    if (metric.includes('rating')) {
      const ratings = ['A', 'B', 'C', 'D', 'E'];
      const index = parseInt(value) - 1;
      return ratings[index] || value;
    }
    
    // Handle large numbers
    const num = parseFloat(value);
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    
    return value;
  };

  const getRatingColor = (rating) => {
    switch (rating) {
      case '1':
      case 'A':
        return '#52c41a';
      case '2':
      case 'B':
        return '#95de64';
      case '3':
      case 'C':
        return '#faad14';
      case '4':
      case 'D':
        return '#ff7a45';
      case '5':
      case 'E':
        return '#f5222d';
      default:
        return '#8c8c8c';
    }
  };

  // Group metrics by category
  const getMetricsByCategory = () => {
    const categories = {
      'Reliability': ['bugs', 'reliability rating'],
      'Security': ['vulnerabilities', 'security rating', 'security hotspots'],
      'Maintainability': ['code smells', 'sqale rating', 'technical debt'],
      'Coverage': ['coverage'],
      'Duplications': ['duplicated lines density'],
      'Size': ['ncloc', 'complexity', 'cognitive complexity']
    };

    const grouped = {};
    Object.keys(categories).forEach(category => {
      grouped[category] = results.metrics.filter(m => 
        categories[category].some(key => m.name.toLowerCase().includes(key.toLowerCase()))
      );
    });

    return grouped;
  };

  const metricsGroups = getMetricsByCategory();

  return (
    <div className="sonar-results-view">
      {/* Quality Gate Status Banner */}
      <div 
        className="quality-gate-banner"
        style={{ 
          backgroundColor: getQualityGateColor(results.qualityGateStatus),
          opacity: 0.1
        }}
      >
        <div className="quality-gate-content">
          <div className="quality-gate-icon">
            {results.qualityGateStatus === 'OK' || results.qualityGateStatus === 'PASSED' ? '✓' : '✗'}
          </div>
          <div className="quality-gate-text">
            <div className="quality-gate-label">Quality Gate</div>
            <div 
              className="quality-gate-status"
              style={{ color: getQualityGateColor(results.qualityGateStatus) }}
            >
              {results.qualityGateStatus}
            </div>
          </div>
          <a 
            href={results.dashboardUrl} 
            target="_blank" 
            rel="noopener noreferrer"
            className="sonar-link-btn"
          >
            View on SonarCloud →
          </a>
        </div>
      </div>

      {/* Tabs */}
      <div className="results-tabs">
        <button
          className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab-btn ${activeTab === 'metrics' ? 'active' : ''}`}
          onClick={() => setActiveTab('metrics')}
        >
          Metrics
        </button>
        <button
          className={`tab-btn ${activeTab === 'issues' ? 'active' : ''}`}
          onClick={() => setActiveTab('issues')}
        >
          Issues ({results.issues.bugs + results.issues.vulnerabilities + results.issues.codeSmells})
        </button>
        <button
          className={`tab-btn ${activeTab === 'conditions' ? 'active' : ''}`}
          onClick={() => setActiveTab('conditions')}
        >
          Quality Gate Conditions
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="overview-tab">
            {/* Key Metrics Cards */}
            <div className="key-metrics-grid">
              <div className="metric-card-large">
                <div className="metric-icon">🐛</div>
                <div className="metric-details">
                  <div className="metric-value">{results.issues.bugs}</div>
                  <div className="metric-label">Bugs</div>
                </div>
              </div>
              
              <div className="metric-card-large">
                <div className="metric-icon">🔒</div>
                <div className="metric-details">
                  <div className="metric-value">{results.issues.vulnerabilities}</div>
                  <div className="metric-label">Vulnerabilities</div>
                </div>
              </div>
              
              <div className="metric-card-large">
                <div className="metric-icon">👃</div>
                <div className="metric-details">
                  <div className="metric-value">{results.issues.codeSmells}</div>
                  <div className="metric-label">Code Smells</div>
                </div>
              </div>
              
              <div className="metric-card-large">
                <div className="metric-icon">🔥</div>
                <div className="metric-details">
                  <div className="metric-value">{results.issues.securityHotspots}</div>
                  <div className="metric-label">Security Hotspots</div>
                </div>
              </div>
            </div>

            {/* Coverage and Duplication */}
            <div className="coverage-section">
              <div className="coverage-card">
                <div className="coverage-header">
                  <span className="coverage-label">Code Coverage</span>
                  <span className="coverage-value">{results.coverage || 'N/A'}%</span>
                </div>
                <div className="coverage-bar">
                  <div 
                    className="coverage-fill"
                    style={{ width: `${results.coverage || 0}%` }}
                  />
                </div>
              </div>
              
              <div className="coverage-card">
                <div className="coverage-header">
                  <span className="coverage-label">Duplications</span>
                  <span className="coverage-value">{results.duplications || 'N/A'}%</span>
                </div>
                <div className="coverage-bar">
                  <div 
                    className="coverage-fill duplication"
                    style={{ width: `${results.duplications || 0}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Ratings */}
            <div className="ratings-section">
              <h3>Ratings</h3>
              <div className="ratings-grid">
                {results.metrics
                  .filter(m => m.name.toLowerCase().includes('rating'))
                  .map((metric, index) => {
                    const ratingValue = formatMetricValue(metric.value, metric.name);
                    return (
                      <div key={index} className="rating-card">
                        <div className="rating-label">{metric.name}</div>
                        <div 
                          className="rating-badge"
                          style={{ 
                            backgroundColor: getRatingColor(ratingValue),
                            color: 'white'
                          }}
                        >
                          {ratingValue}
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          </div>
        )}

        {/* Metrics Tab */}
        {activeTab === 'metrics' && (
          <div className="metrics-tab">
            {Object.entries(metricsGroups).map(([category, metrics]) => (
              metrics.length > 0 && (
                <div key={category} className="metrics-category">
                  <h3>{category}</h3>
                  <div className="metrics-grid">
                    {metrics.map((metric, index) => (
                      <div key={index} className="metric-card">
                        <div className="metric-name">{metric.name}</div>
                        <div className="metric-value">
                          {formatMetricValue(metric.value, metric.name)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )
            ))}
          </div>
        )}

        {/* Issues Tab */}
        {activeTab === 'issues' && (
          <div className="issues-tab">
            {/* Issue Filters */}
            <div className="issue-filters">
              <div className="filter-group">
                <label>Type:</label>
                <select 
                  value={issueFilters.types}
                  onChange={(e) => setIssueFilters({...issueFilters, types: e.target.value})}
                >
                  <option value="">All</option>
                  <option value="BUG">Bugs</option>
                  <option value="VULNERABILITY">Vulnerabilities</option>
                  <option value="CODE_SMELL">Code Smells</option>
                </select>
              </div>
              
              <div className="filter-group">
                <label>Severity:</label>
                <select 
                  value={issueFilters.severities}
                  onChange={(e) => setIssueFilters({...issueFilters, severities: e.target.value})}
                >
                  <option value="">All</option>
                  <option value="BLOCKER">Blocker</option>
                  <option value="CRITICAL">Critical</option>
                  <option value="MAJOR">Major</option>
                  <option value="MINOR">Minor</option>
                  <option value="INFO">Info</option>
                </select>
              </div>
            </div>

            {/* Issues List */}
            {loadingIssues ? (
              <div className="loading-state">Loading issues...</div>
            ) : issues.length > 0 ? (
              <div className="issues-list">
                {issues.map((issue, index) => (
                  <div key={index} className="issue-item">
                    <div className="issue-header">
                      <div className="issue-type-icon">{getTypeIcon(issue.type)}</div>
                      <div className="issue-meta">
                        <span 
                          className="issue-severity"
                          style={{ 
                            backgroundColor: getSeverityColor(issue.severity),
                            color: 'white'
                          }}
                        >
                          {issue.severity}
                        </span>
                        <span className="issue-type">{issue.type}</span>
                      </div>
                    </div>
                    <div className="issue-message">{issue.message}</div>
                    <div className="issue-location">
                      <span className="issue-file">{issue.component.split(':').pop()}</span>
                      {issue.line && <span className="issue-line">Line {issue.line}</span>}
                    </div>
                    <div className="issue-rule">{issue.rule}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">No issues found</div>
            )}
          </div>
        )}

        {/* Quality Gate Conditions Tab */}
        {activeTab === 'conditions' && (
          <div className="conditions-tab">
            {results.qualityGateConditions && results.qualityGateConditions.length > 0 ? (
              <div className="conditions-list">
                {results.qualityGateConditions.map((condition, index) => (
                  <div 
                    key={index} 
                    className={`condition-item ${condition.status.toLowerCase()}`}
                  >
                    <div className="condition-status-icon">
                      {condition.status === 'OK' ? '✓' : '✗'}
                    </div>
                    <div className="condition-details">
                      <div className="condition-metric">{condition.metric}</div>
                      <div className="condition-values">
                        <span className="condition-actual">
                          Actual: {condition.actualValue || 'N/A'}
                        </span>
                        {condition.errorThreshold && (
                          <span className="condition-threshold">
                            Threshold: {condition.comparator} {condition.errorThreshold}
                          </span>
                        )}
                      </div>
                    </div>
                    <div 
                      className="condition-status-badge"
                      style={{ 
                        backgroundColor: getQualityGateColor(condition.status),
                        color: 'white'
                      }}
                    >
                      {condition.status}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">No quality gate conditions defined</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SonarResultsView;
