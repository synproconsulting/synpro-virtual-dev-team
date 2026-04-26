import React, { useState, useEffect } from 'react';
import { fetchOpenPRs, triggerAutoReview, getReviewStatus } from '../api/prApi';
import './AutoReviewPR.css';

const AutoReviewPR = () => {
  const [prs, setPRs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [reviewingPRs, setReviewingPRs] = useState(new Set());
  const [reviewStatuses, setReviewStatuses] = useState({});
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    repository: 'all',
    author: 'all'
  });

  useEffect(() => {
    loadPRs();
  }, []);

  const loadPRs = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await fetchOpenPRs();
      setPRs(data);
    } catch (err) {
      setError(err.message || 'Failed to load PRs');
    } finally {
      setLoading(false);
    }
  };

  const handleAutoReview = async (prId, prNumber, repo) => {
    setReviewingPRs(prev => new Set(prev).add(prId));
    
    try {
      const result = await triggerAutoReview(prNumber, repo);
      
      setReviewStatuses(prev => ({
        ...prev,
        [prId]: {
          status: 'completed',
          message: 'Auto-review triggered successfully',
          details: result
        }
      }));

      // Poll for review status
      pollReviewStatus(prId, prNumber, repo);
    } catch (err) {
      setReviewStatuses(prev => ({
        ...prev,
        [prId]: {
          status: 'failed',
          message: err.message || 'Auto-review failed'
        }
      }));
      setReviewingPRs(prev => {
        const newSet = new Set(prev);
        newSet.delete(prId);
        return newSet;
      });
    }
  };

  const pollReviewStatus = async (prId, prNumber, repo) => {
    let attempts = 0;
    const maxAttempts = 10;
    
    const interval = setInterval(async () => {
      attempts++;
      
      try {
        const status = await getReviewStatus(prNumber, repo);
        
        if (status.completed || attempts >= maxAttempts) {
          clearInterval(interval);
          setReviewingPRs(prev => {
            const newSet = new Set(prev);
            newSet.delete(prId);
            return newSet;
          });
          
          setReviewStatuses(prev => ({
            ...prev,
            [prId]: {
              status: status.completed ? 'completed' : 'timeout',
              message: status.message,
              details: status.details
            }
          }));
        }
      } catch (err) {
        clearInterval(interval);
        setReviewingPRs(prev => {
          const newSet = new Set(prev);
          newSet.delete(prId);
          return newSet;
        });
      }
    }, 3000);
  };

  const filteredPRs = prs.filter(pr => {
    if (filters.repository !== 'all' && pr.repository !== filters.repository) {
      return false;
    }
    if (filters.author !== 'all' && pr.author !== filters.author) {
      return false;
    }
    return true;
  });

  const uniqueRepos = [...new Set(prs.map(pr => pr.repository))];
  const uniqueAuthors = [...new Set(prs.map(pr => pr.author))];

  return (
    <div className="auto-review-container">
      <div className="header">
        <h2>Auto Review PRs</h2>
        <button onClick={loadPRs} disabled={loading} className="refresh-button">
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <div className="filters">
        <select
          value={filters.repository}
          onChange={(e) => setFilters(prev => ({ ...prev, repository: e.target.value }))}
        >
          <option value="all">All Repositories</option>
          {uniqueRepos.map(repo => (
            <option key={repo} value={repo}>{repo}</option>
          ))}
        </select>

        <select
          value={filters.author}
          onChange={(e) => setFilters(prev => ({ ...prev, author: e.target.value }))}
        >
          <option value="all">All Authors</option>
          {uniqueAuthors.map(author => (
            <option key={author} value={author}>{author}</option>
          ))}
        </select>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="pr-list">
        {loading && prs.length === 0 ? (
          <div className="loading-state">Loading PRs...</div>
        ) : filteredPRs.length === 0 ? (
          <div className="empty-state">No open PRs found</div>
        ) : (
          filteredPRs.map(pr => (
            <div key={pr.id} className="pr-card">
              <div className="pr-header">
                <h3>
                  <a href={pr.url} target="_blank" rel="noopener noreferrer">
                    {pr.title}
                  </a>
                </h3>
                <span className="pr-number">#{pr.number}</span>
              </div>
              
              <div className="pr-meta">
                <span className="repo">{pr.repository}</span>
                <span className="author">by {pr.author}</span>
                <span className="date">{new Date(pr.createdAt).toLocaleDateString()}</span>
              </div>

              <div className="pr-actions">
                <button
                  onClick={() => handleAutoReview(pr.id, pr.number, pr.repository)}
                  disabled={reviewingPRs.has(pr.id)}
                  className="review-button"
                >
                  {reviewingPRs.has(pr.id) ? 'Reviewing...' : 'Trigger Auto Review'}
                </button>
              </div>

              {reviewStatuses[pr.id] && (
                <div className={`review-status status-${reviewStatuses[pr.id].status}`}>
                  <strong>{reviewStatuses[pr.id].status.toUpperCase()}:</strong> {reviewStatuses[pr.id].message}
                  {reviewStatuses[pr.id].details && (
                    <div className="status-details">
                      {reviewStatuses[pr.id].details.commentUrl && (
                        <a href={reviewStatuses[pr.id].details.commentUrl} target="_blank" rel="noopener noreferrer">
                          View Review Comment
                        </a>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default AutoReviewPR;
