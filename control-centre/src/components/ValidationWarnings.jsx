/**
 * ValidationWarnings.jsx
 * ──────────────────────
 * Displays PM Agent validation warnings for stories missing execution_order
 * or other critical fields required for automated workflow.
 */

import React, { useState, useEffect } from 'react';
import { AlertTriangle, ExternalLink, RefreshCw, X } from 'lucide-react';
import './ValidationWarnings.css';

const JIRA_URL = import.meta.env.VITE_JIRA_URL || "https://synproconsulting.atlassian.net";

const WARNING_TYPES = {
  MISSING_EXECUTION_ORDER: {
    icon: '⚠️',
    color: '#f97316',
    severity: 'critical',
    title: 'Missing Execution Order'
  },
  MISSING_EPIC: {
    icon: 'ℹ️',
    color: '#3b82f6',
    severity: 'info',
    title: 'Not Linked to Epic'
  },
  LONG_SUMMARY: {
    icon: 'ℹ️',
    color: '#3b82f6',
    severity: 'info',
    title: 'Long Summary'
  },
};

const ValidationWarning = ({ warning, onDismiss }) => {
  const typeConfig = WARNING_TYPES[warning.type] || {
    icon: '⚠️',
    color: '#fbbf24',
    severity: 'warning',
    title: 'Validation Warning'
  };

  return (
    <div 
      className={`validation-warning validation-warning-${typeConfig.severity}`}
      style={{ borderLeftColor: typeConfig.color }}
    >
      <div className="validation-warning-header">
        <span className="validation-warning-icon">{typeConfig.icon}</span>
        <span className="validation-warning-title">{typeConfig.title}</span>
        {warning.issue_key && (
          <a
            href={`${JIRA_URL}/browse/${warning.issue_key}`}
            target="_blank"
            rel="noopener noreferrer"
            className="validation-warning-issue-link"
          >
            {warning.issue_key}
            <ExternalLink size={12} />
          </a>
        )}
        {onDismiss && (
          <button
            className="validation-warning-dismiss"
            onClick={() => onDismiss(warning)}
            aria-label="Dismiss"
          >
            <X size={14} />
          </button>
        )}
      </div>
      <div className="validation-warning-message">{warning.message}</div>
      {warning.suggestion && (
        <div className="validation-warning-suggestion">
          💡 {warning.suggestion}
        </div>
      )}
    </div>
  );
};

const ValidationWarnings = ({ 
  warnings = [], 
  loading = false, 
  onRefresh = null,
  dismissible = false,
  className = '',
  title = 'Validation Warnings',
  showCount = true 
}) => {
  const [dismissed, setDismissed] = useState(new Set());
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleDismiss = (warning) => {
    if (!dismissible) return;
    setDismissed(prev => new Set([...prev, warning.id || warning.issue_key]));
  };

  const handleRefresh = async () => {
    if (!onRefresh || isRefreshing) return;
    setIsRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setIsRefreshing(false);
    }
  };

  const visibleWarnings = warnings.filter(
    w => !dismissed.has(w.id || w.issue_key)
  );

  // Group by severity
  const critical = visibleWarnings.filter(w => {
    const type = WARNING_TYPES[w.type];
    return type?.severity === 'critical';
  });
  const other = visibleWarnings.filter(w => {
    const type = WARNING_TYPES[w.type];
    return type?.severity !== 'critical';
  });

  if (loading) {
    return (
      <div className={`validation-warnings ${className}`}>
        <div className="validation-warnings-loading">
          <RefreshCw size={16} className="spin" />
          <span>Loading validation warnings...</span>
        </div>
      </div>
    );
  }

  if (visibleWarnings.length === 0) {
    return null;
  }

  return (
    <div className={`validation-warnings ${className}`}>
      <div className="validation-warnings-header">
        <div className="validation-warnings-title">
          <AlertTriangle size={16} />
          <span>{title}</span>
          {showCount && (
            <span className="validation-warnings-count">
              {visibleWarnings.length}
            </span>
          )}
        </div>
        {onRefresh && (
          <button
            className="validation-warnings-refresh"
            onClick={handleRefresh}
            disabled={isRefreshing}
            aria-label="Refresh warnings"
          >
            <RefreshCw size={14} className={isRefreshing ? 'spin' : ''} />
          </button>
        )}
      </div>

      <div className="validation-warnings-list">
        {critical.length > 0 && (
          <div className="validation-warnings-section">
            <div className="validation-warnings-section-title">
              Critical Issues ({critical.length})
            </div>
            {critical.map((warning, idx) => (
              <ValidationWarning
                key={warning.id || warning.issue_key || idx}
                warning={warning}
                onDismiss={dismissible ? handleDismiss : null}
              />
            ))}
          </div>
        )}

        {other.length > 0 && (
          <div className="validation-warnings-section">
            {critical.length > 0 && (
              <div className="validation-warnings-section-title">
                Informational ({other.length})
              </div>
            )}
            {other.map((warning, idx) => (
              <ValidationWarning
                key={warning.id || warning.issue_key || idx}
                warning={warning}
                onDismiss={dismissible ? handleDismiss : null}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ValidationWarnings;
