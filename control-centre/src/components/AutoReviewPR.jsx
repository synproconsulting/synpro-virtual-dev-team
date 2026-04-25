import React, { useState, useEffect } from 'react';
import { GitPullRequest, Check, X, RefreshCw, Clock, ExternalLink } from 'lucide-react';
import './AutoReviewPR.css';

const AutoReviewPR = ({ projectId }) => {
  const [prs, setPrs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [reviewingPRs, setReviewingPRs] = useState(new Set());

  const fetchPRs = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/pull-requests?project_id=${projectId}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch pull requests');
      }

      setPrs(data.pull_requests || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const triggerAutoReview = async (prId) => {
    setReviewingPRs(prev => new Set(prev).add(prId));

    try {
      const response = await fetch('/api/pull-requests/auto-review', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pr_id: prId, project_id: projectId }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to trigger auto-review');
      }

      // Update PR status in the list
      setPrs(prevPrs =>
        prevPrs.map(pr =>
          pr.id === prId
            ? { ...pr, auto_review_status: 'in_progress', review_id: data.review_id }
            : pr
        )
      );
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      setReviewingPRs(prev => {
        const newSet = new Set(prev);
        newSet.delete(prId);
        return newSet;
      });
    }
  };

  useEffect(() => {
    if (projectId) {
      fetchPRs();
    }
  }, [projectId]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <Check className="icon status-completed" />;
      case 'in_progress':
        return <Clock className="icon status-in-progress" />;
      case 'failed':
        return <X className="icon status-failed" />;
      default:
        return <GitPullRequest className="icon" />;
    }
  };

  return (
    <div className="auto-review-container">
      <div className="auto-review-header">
        <h3>Auto Review Pull Requests</h3>
        <button
          className="refresh-button"
          onClick={fetchPRs}
          disabled={loading}
        >
          <RefreshCw className={`icon ${loading ? 'spinning' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="error-banner">
          <X className="icon" />
          {error}
        </div>
      )}

      <div className="pr-list">
        {loading && prs.length === 0 ? (
          <div className="loading-state">Loading pull requests...</div>
        ) : prs.length === 0 ? (
          <div className="empty-state">No open pull requests found</div>
        ) : (
          prs.map(pr => (
            <div key={pr.id} className="pr-card">
              <div className="pr-header">
                <div className="pr-title">
                  {getStatusIcon(pr.auto_review_status)}
                  <span>{pr.title}</span>
                </div>
                <a
                  href={pr.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="pr-link"
                >
                  <ExternalLink className="icon" />
                </a>
              </div>

              <div className="pr-meta">
                <span className="pr-author">by {pr.author}</span>
                <span className="pr-branch">{pr.source_branch} → {pr.target_branch}</span>
              </div>

              {pr.auto_review_status && pr.auto_review_status !== 'not_started' ? (
                <div className="review-status">
                  Status: <span className={`status-badge ${pr.auto_review_status}`}>
                    {pr.auto_review_status.replace('_', ' ')}
                  </span>
                </div>
              ) : (
                <button
                  className="review-button"
                  onClick={() => triggerAutoReview(pr.id)}
                  disabled={reviewingPRs.has(pr.id)}
                >
                  {reviewingPRs.has(pr.id) ? 'Triggering...' : 'Trigger Auto Review'}
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default AutoReviewPR;
