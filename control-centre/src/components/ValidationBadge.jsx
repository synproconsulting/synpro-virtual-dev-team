/**
 * ValidationBadge.jsx
 * ───────────────────
 * Compact badge showing validation warning count with tooltip
 */

import React, { useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import './ValidationBadge.css';

const ValidationBadge = ({ 
  count = 0, 
  criticalCount = 0,
  onClick = null,
  size = 'medium',
  showLabel = true,
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  if (count === 0) {
    return null;
  }

  const hasCritical = criticalCount > 0;
  const className = `validation-badge validation-badge-${size} ${hasCritical ? 'validation-badge-critical' : 'validation-badge-warning'}`;

  const badge = (
    <div
      className={className}
      onClick={onClick}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      <AlertTriangle size={size === 'small' ? 12 : 14} />
      <span className="validation-badge-count">{count}</span>
      {showLabel && size !== 'small' && (
        <span className="validation-badge-label">
          {hasCritical ? 'Issues' : 'Warnings'}
        </span>
      )}
      {showTooltip && (
        <div className="validation-badge-tooltip">
          {hasCritical ? (
            <>
              <strong>{criticalCount}</strong> critical issue{criticalCount !== 1 ? 's' : ''}
              {count > criticalCount && (
                <>, <strong>{count - criticalCount}</strong> other{count - criticalCount !== 1 ? 's' : ''}</>
              )}
            </>
          ) : (
            <>
              <strong>{count}</strong> validation warning{count !== 1 ? 's' : ''}
            </>
          )}
        </div>
      )}
    </div>
  );

  return badge;
};

export default ValidationBadge;
