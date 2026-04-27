import React from 'react';
import './NotificationItem.css';

const NotificationItem = ({ notification, onMarkAsRead }) => {
  const { id, type, title, message, timestamp, read, severity, metadata } = notification;

  const getIcon = () => {
    switch (type) {
      case 'sprint':
        return '🏃';
      case 'deployment':
        return '🚀';
      case 'workflow':
        return '⚙️';
      case 'sonarcloud':
        return '🔍';
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      case 'success':
        return '✅';
      case 'info':
      default:
        return 'ℹ️';
    }
  };

  const getSeverityClass = () => {
    switch (severity) {
      case 'critical':
        return 'severity-critical';
      case 'high':
        return 'severity-high';
      case 'medium':
        return 'severity-medium';
      case 'low':
        return 'severity-low';
      default:
        return '';
    }
  };

  const formatTimestamp = (ts) => {
    const date = new Date(ts);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  };

  const handleClick = () => {
    if (!read) {
      onMarkAsRead(id);
    }
  };

  return (
    <div
      className={`notification-item ${read ? 'read' : 'unread'} ${getSeverityClass()}`}
      onClick={handleClick}
    >
      <div className="notification-icon">{getIcon()}</div>
      <div className="notification-content">
        <div className="notification-header-row">
          <h4 className="notification-title">{title}</h4>
          <span className="notification-timestamp">{formatTimestamp(timestamp)}</span>
        </div>
        <p className="notification-message">{message}</p>
        {metadata && (
          <div className="notification-metadata">
            {metadata.sprintNumber && (
              <span className="metadata-tag">Sprint {metadata.sprintNumber}</span>
            )}
            {metadata.workflow && (
              <span className="metadata-tag">{metadata.workflow}</span>
            )}
            {metadata.environment && (
              <span className="metadata-tag">{metadata.environment}</span>
            )}
            {metadata.branch && (
              <span className="metadata-tag">{metadata.branch}</span>
            )}
          </div>
        )}
      </div>
      {!read && <div className="unread-indicator"></div>}
    </div>
  );
};

export default NotificationItem;