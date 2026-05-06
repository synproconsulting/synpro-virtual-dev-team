/**
 * PMValidationDashboard.jsx
 * ─────────────────────────
 * Dashboard view for PM Agent validation warnings
 * Shows all validation issues that need attention before sprint execution
 */

import React, { useState } from 'react';
import ValidationWarnings from './ValidationWarnings';
import ValidationBadge from './ValidationBadge';
import { useValidationWarnings } from '../hooks/useValidationWarnings';
import { CheckCircle, RefreshCw } from 'lucide-react';
import './PMValidationDashboard.css';

const PMValidationDashboard = ({ sprintId = null }) => {
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(false);
  
  const {
    warnings,
    loading,
    error,
    lastFetch,
    refresh,
    hasWarnings,
    criticalCount,
    warningCount,
    infoCount,
  } = useValidationWarnings({
    sprintId,
    autoRefresh: autoRefreshEnabled,
    refreshInterval: 300000, // 5 minutes
  });

  const handleRefresh = async () => {
    await refresh();
  };

  const formatLastFetch = () => {
    if (!lastFetch) return 'Never';
    const now = new Date();
    const diff = Math.floor((now - lastFetch) / 1000);
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return lastFetch.toLocaleDateString();
  };

  return (
    <div className="pm-validation-dashboard">
      <div className="pm-validation-header">
        <div className="pm-validation-header-content">
          <h2 className="pm-validation-title">
            PM Agent Validation
          </h2>
          <p className="pm-validation-subtitle">
            Review and resolve validation warnings before executing sprint
          </p>
        </div>
        
        <div className="pm-validation-controls">
          <div className="pm-validation-auto-refresh">
            <label>
              <input
                type="checkbox"
                checked={autoRefreshEnabled}
                onChange={(e) => setAutoRefreshEnabled(e.target.checked)}
              />
              <span>Auto-refresh</span>
            </label>
          </div>
          <button
            className="pm-validation-refresh-btn"
            onClick={handleRefresh}
            disabled={loading}
          >
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      <div className="pm-validation-summary">
        <div className="pm-validation-summary-cards">
          <div className={`pm-validation-summary-card ${criticalCount > 0 ? 'critical' : 'success'}`}>
            <div className="pm-validation-summary-card-value">
              {criticalCount}
            </div>
            <div className="pm-validation-summary-card-label">
              Critical Issues
            </div>
          </div>

          <div className="pm-validation-summary-card info">
            <div className="pm-validation-summary-card-value">
              {warningCount + infoCount}
            </div>
            <div className="pm-validation-summary-card-label">
              Warnings
            </div>
          </div>

          <div className={`pm-validation-summary-card ${hasWarnings ? 'pending' : 'success'}`}>
            <div className="pm-validation-summary-card-icon">
              {hasWarnings ? '⚠️' : <CheckCircle size={32} />}
            </div>
            <div className="pm-validation-summary-card-label">
              {hasWarnings ? 'Issues Found' : 'All Clear'}
            </div>
          </div>
        </div>

        <div className="pm-validation-summary-footer">
          <span className="pm-validation-last-check">
            Last checked: {formatLastFetch()}
          </span>
        </div>
      </div>

      {error && (
        <div className="pm-validation-error">
          <span className="pm-validation-error-icon">⚠️</span>
          <span className="pm-validation-error-message">
            Failed to load validation warnings: {error}
          </span>
        </div>
      )}

      {!hasWarnings && !loading && !error && (
        <div className="pm-validation-success">
          <CheckCircle size={48} color="#4ade80" />
          <h3>All Validations Passed</h3>
          <p>
            All stories have required fields set correctly. The sprint is ready for execution.
          </p>
        </div>
      )}

      {hasWarnings && (
        <div className="pm-validation-content">
          <ValidationWarnings
            warnings={warnings}
            loading={loading}
            onRefresh={handleRefresh}
            dismissible={false}
            title=""
            showCount={false}
          />
        </div>
      )}

      <div className="pm-validation-help">
        <h4>About Validation Warnings</h4>
        <div className="pm-validation-help-content">
          <div className="pm-validation-help-item">
            <span className="pm-validation-help-icon critical">⚠️</span>
            <div>
              <strong>Critical Issues</strong>
              <p>
                Must be resolved before sprint execution. Stories without <code>execution_order</code> 
                will not be picked up by the Orchestrator.
              </p>
            </div>
          </div>
          <div className="pm-validation-help-item">
            <span className="pm-validation-help-icon info">ℹ️</span>
            <div>
              <strong>Informational Warnings</strong>
              <p>
                Best practice recommendations. Won't block sprint execution but should be reviewed 
                for better organization and clarity.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PMValidationDashboard;
