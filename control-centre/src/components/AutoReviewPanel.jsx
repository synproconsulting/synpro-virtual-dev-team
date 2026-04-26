import React, { useState, useEffect } from 'react';
import { enableAutoReview, disableAutoReview, getAutoReviewStatus } from '../api/autoReviewApi';
import './AutoReviewPanel.css';

const AutoReviewPanel = () => {
  const [loading, setLoading] = useState(false);
  const [statusLoading, setStatusLoading] = useState(true);
  const [error, setError] = useState(null);
  const [prUrl, setPrUrl] = useState('');
  const [isEnabled, setIsEnabled] = useState(false);
  const [reviewConfig, setReviewConfig] = useState({
    auto_approve: false,
    check_tests: true,
    check_linting: true,
    require_description: true
  });
  const [activeReviews, setActiveReviews] = useState([]);

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    setStatusLoading(true);
    try {
      const status = await getAutoReviewStatus();
      setActiveReviews(status.active_reviews || []);
    } catch (err) {
      console.error('Failed to fetch auto-review status:', err);
    } finally {
      setStatusLoading(false);
    }
  };

  const handleEnable = async () => {
    if (!prUrl.trim()) {
      setError('PR URL is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await enableAutoReview({
        pr_url: prUrl,
        config: reviewConfig
      });
      setIsEnabled(true);
      setPrUrl('');
      await fetchStatus();
    } catch (err) {
      setError(err.message || 'Failed to enable auto-review');
    } finally {
      setLoading(false);
    }
  };

  const handleDisable = async (prId) => {
    try {
      await disableAutoReview(prId);
      await fetchStatus();
    } catch (err) {
      setError(err.message || 'Failed to disable auto-review');
    }
  };

  return (
    <div className="auto-review-panel">
      <h2>Auto Review per PR</h2>

      <div className="review-form">
        <div className="form-group">
          <label htmlFor="prUrl">Pull Request URL:</label>
          <input
            id="prUrl"
            type="text"
            value={prUrl}
            onChange={(e) => setPrUrl(e.target.value)}
            placeholder="https://github.com/owner/repo/pull/123"
            disabled={loading}
          />
        </div>

        <div className="config-section">
          <h3>Review Configuration</h3>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={reviewConfig.check_tests}
              onChange={(e) => setReviewConfig({ ...reviewConfig, check_tests: e.target.checked })}
              disabled={loading}
            />
            <span>Verify tests pass</span>
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={reviewConfig.check_linting}
              onChange={(e) => setReviewConfig({ ...reviewConfig, check_linting: e.target.checked })}
              disabled={loading}
            />
            <span>Check linting/formatting</span>
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={reviewConfig.require_description}
              onChange={(e) => setReviewConfig({ ...reviewConfig, require_description: e.target.checked })}
              disabled={loading}
            />
            <span>Require PR description</span>
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={reviewConfig.auto_approve}
              onChange={(e) => setReviewConfig({ ...reviewConfig, auto_approve: e.target.checked })}
              disabled={loading}
            />
            <span>Auto-approve if all checks pass</span>
          </label>
        </div>

        <button
          className="enable-button"
          onClick={handleEnable}
          disabled={loading}
        >
          {loading ? 'Enabling...' : 'Enable Auto Review'}
        </button>
      </div>

      {error && <div className="message error-message">{error}</div>}

      <div className="active-reviews-section">
        <h3>Active Auto Reviews</h3>
        {statusLoading ? (
          <p className="loading-text">Loading...</p>
        ) : activeReviews.length === 0 ? (
          <p className="empty-state">No active auto-reviews</p>
        ) : (
          <ul className="reviews-list">
            {activeReviews.map((review) => (
              <li key={review.id} className="review-item">
                <div className="review-info">
                  <a href={review.pr_url} target="_blank" rel="noopener noreferrer">
                    {review.pr_title || review.pr_url}
                  </a>
                  <span className="review-status">{review.status}</span>
                </div>
                <button
                  className="disable-button"
                  onClick={() => handleDisable(review.id)}
                >
                  Disable
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default AutoReviewPanel;
