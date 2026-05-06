/**
 * ValidationExample.jsx
 * ─────────────────────
 * Example implementation showing how to integrate validation warnings
 * into existing components. This file serves as a reference for developers.
 */

import React, { useState } from 'react';
import ValidationWarnings from './ValidationWarnings';
import ValidationBadge from './ValidationBadge';
import PMValidationDashboard from './PMValidationDashboard';
import { useValidationWarnings } from '../hooks/useValidationWarnings';

/**
 * Example 1: Simple inline validation warnings
 */
export function InlineValidationExample() {
  const { warnings, loading, refresh } = useValidationWarnings();

  return (
    <div style={{ padding: '20px' }}>
      <h2>Sprint Planning</h2>
      
      {/* Show warnings inline with your content */}
      {warnings.length > 0 && (
        <ValidationWarnings
          warnings={warnings}
          loading={loading}
          onRefresh={refresh}
        />
      )}
      
      {/* Your existing content */}
      <div>Your sprint planning UI...</div>
    </div>
  );
}

/**
 * Example 2: Badge in header with expandable panel
 */
export function BadgeWithPanelExample() {
  const [showWarnings, setShowWarnings] = useState(false);
  const { warnings, criticalCount, refresh } = useValidationWarnings();

  return (
    <div>
      <header style={{ display: 'flex', justifyContent: 'space-between', padding: '20px' }}>
        <h1>Sprint Dashboard</h1>
        
        {/* Badge in header */}
        {warnings.length > 0 && (
          <ValidationBadge
            count={warnings.length}
            criticalCount={criticalCount}
            onClick={() => setShowWarnings(true)}
            showLabel={true}
          />
        )}
      </header>

      {/* Expandable panel */}
      {showWarnings && (
        <div style={{ padding: '20px' }}>
          <ValidationWarnings
            warnings={warnings}
            onRefresh={refresh}
            dismissible={true}
          />
          <button onClick={() => setShowWarnings(false)}>
            Close
          </button>
        </div>
      )}
    </div>
  );
}

/**
 * Example 3: Full validation dashboard page
 */
export function ValidationDashboardExample() {
  const [selectedSprintId, setSelectedSprintId] = useState(null);

  return (
    <div style={{ padding: '20px' }}>
      {/* Sprint selector */}
      <div style={{ marginBottom: '20px' }}>
        <label>
          Select Sprint:
          <select 
            value={selectedSprintId || ''} 
            onChange={(e) => setSelectedSprintId(e.target.value || null)}
          >
            <option value="">All Sprints</option>
            <option value="123">Sprint 1</option>
            <option value="124">Sprint 2</option>
          </select>
        </label>
      </div>

      {/* Full dashboard */}
      <PMValidationDashboard sprintId={selectedSprintId} />
    </div>
  );
}

/**
 * Example 4: Integration with PM Agent Chat
 */
export function PMAgentChatWithValidation() {
  const [messages, setMessages] = useState([]);
  const { warnings, hasWarnings, criticalCount } = useValidationWarnings();

  return (
    <div className="pm-agent-chat">
      {/* Show critical warnings at top of chat */}
      {hasWarnings && criticalCount > 0 && (
        <div style={{ 
          padding: '12px', 
          background: 'rgba(249, 115, 22, 0.1)',
          borderBottom: '1px solid rgba(249, 115, 22, 0.3)'
        }}>
          <ValidationBadge
            count={warnings.length}
            criticalCount={criticalCount}
            size="small"
            showLabel={true}
          />
          <span style={{ marginLeft: '10px', fontSize: '13px' }}>
            Please review validation warnings before executing sprint
          </span>
        </div>
      )}

      {/* Chat messages */}
      <div className="chat-messages">
        {messages.map(msg => (
          <div key={msg.id}>{msg.content}</div>
        ))}
      </div>

      {/* Show warnings in sidebar or bottom panel */}
      {hasWarnings && (
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '12px' }}>
          <ValidationWarnings
            warnings={warnings.filter(w => w.severity === 'critical')}
            title="Critical Issues"
            showCount={true}
          />
        </div>
      )}
    </div>
  );
}

/**
 * Example 5: Auto-refresh with real-time updates
 */
export function AutoRefreshValidationExample() {
  const { 
    warnings, 
    loading, 
    lastFetch,
    refresh,
    hasWarnings,
    criticalCount 
  } = useValidationWarnings({
    autoRefresh: true,      // Enable auto-refresh
    refreshInterval: 60000, // Check every 1 minute
  });

  const formatLastFetch = () => {
    if (!lastFetch) return 'Never';
    return lastFetch.toLocaleTimeString();
  };

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between',
        marginBottom: '16px',
        fontSize: '12px',
        color: 'var(--muted)'
      }}>
        <span>Last updated: {formatLastFetch()}</span>
        <span>
          {loading ? 'Checking...' : `${criticalCount} critical issues`}
        </span>
      </div>

      {hasWarnings ? (
        <ValidationWarnings
          warnings={warnings}
          loading={loading}
          onRefresh={refresh}
        />
      ) : (
        <div style={{ 
          padding: '40px', 
          textAlign: 'center',
          color: 'var(--muted)'
        }}>
          ✓ All validations passed
        </div>
      )}
    </div>
  );
}

/**
 * Example 6: Conditional rendering based on sprint state
 */
export function ConditionalValidationExample({ sprint }) {
  const { warnings, criticalCount, hasWarnings } = useValidationWarnings({
    sprintId: sprint?.id,
  });

  // Only show validation for active sprints
  if (sprint?.state !== 'active') {
    return null;
  }

  // Block sprint execution if critical issues exist
  const canExecuteSprint = criticalCount === 0;

  return (
    <div>
      {hasWarnings && (
        <ValidationWarnings warnings={warnings} />
      )}

      <button 
        disabled={!canExecuteSprint}
        title={!canExecuteSprint ? 'Resolve critical issues before executing sprint' : ''}
        style={{
          padding: '10px 20px',
          opacity: canExecuteSprint ? 1 : 0.5,
          cursor: canExecuteSprint ? 'pointer' : 'not-allowed',
        }}
      >
        Execute Sprint
      </button>
    </div>
  );
}

export default {
  InlineValidationExample,
  BadgeWithPanelExample,
  ValidationDashboardExample,
  PMAgentChatWithValidation,
  AutoRefreshValidationExample,
  ConditionalValidationExample,
};
