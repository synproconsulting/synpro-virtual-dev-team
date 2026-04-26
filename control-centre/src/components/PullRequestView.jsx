import React from 'react';
import { Card, CardHeader, CardContent } from './ui/Card';

const PullRequestView = ({ data, compact = false }) => {
  if (!data) {
    return (
      <Card>
        <CardHeader>Pull Requests</CardHeader>
        <CardContent>
          <p className="text-gray-500">No PR data available</p>
        </CardContent>
      </Card>
    );
  }

  const { pullRequests = [], summary = {} } = data;
  const displayPRs = compact ? pullRequests.slice(0, 5) : pullRequests;

  const getStatusColor = (status) => {
    const colors = {
      open: 'bg-green-100 text-green-800 border-green-200',
      draft: 'bg-gray-100 text-gray-800 border-gray-200',
      merged: 'bg-purple-100 text-purple-800 border-purple-200',
      closed: 'bg-red-100 text-red-800 border-red-200'
    };
    return colors[status] || colors.open;
  };

  const getReviewStatus = (pr) => {
    if (pr.approved) return { text: '✓ Approved', color: 'text-green-600' };
    if (pr.changesRequested) return { text: '⚠ Changes Requested', color: 'text-red-600' };
    if (pr.reviewsCount > 0) return { text: '👀 In Review', color: 'text-yellow-600' };
    return { text: '⏳ Awaiting Review', color: 'text-gray-600' };
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Pull Requests</h3>
          <span className="text-sm text-gray-600">
            {summary.open || 0} open
          </span>
        </div>
      </CardHeader>
      <CardContent>
        {!compact && summary.open > 0 && (
          <div className="grid grid-cols-3 gap-4 mb-6">
            <PRMetric label="Open" value={summary.open || 0} />
            <PRMetric label="Merged Today" value={summary.mergedToday || 0} />
            <PRMetric label="Avg Review Time" value={summary.avgReviewTime || 'N/A'} />
          </div>
        )}

        <div className="space-y-3">
          {displayPRs.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No pull requests found</p>
          ) : (
            displayPRs.map((pr) => {
              const reviewStatus = getReviewStatus(pr);
              return (
                <div
                  key={pr.id}
                  className="border rounded-lg p-3 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span
                          className={`text-xs px-2 py-0.5 rounded border ${getStatusColor(pr.state)}`}
                        >
                          {pr.state}
                        </span>
                        {pr.isDraft && (
                          <span className="text-xs px-2 py-0.5 rounded bg-gray-200 text-gray-700">
                            Draft
                          </span>
                        )}
                      </div>
                      <a
                        href={pr.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm font-medium text-blue-600 hover:underline block mb-1"
                      >
                        {pr.title}
                      </a>
                      <div className="flex items-center gap-3 text-xs text-gray-600">
                        <span>#{pr.number}</span>
                        <span>by {pr.author}</span>
                        <span className={reviewStatus.color}>{reviewStatus.text}</span>
                      </div>
                      {pr.ciStatus && (
                        <div className="mt-2">
                          <CIStatusBadge status={pr.ciStatus} />
                        </div>
                      )}
                    </div>
                    <div className="ml-2 text-right">
                      <div className="text-xs text-gray-500">
                        {pr.createdAt}
                      </div>
                      {pr.additions !== undefined && pr.deletions !== undefined && (
                        <div className="text-xs mt-1">
                          <span className="text-green-600">+{pr.additions}</span>
                          {' / '}
                          <span className="text-red-600">-{pr.deletions}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {compact && pullRequests.length > 5 && (
          <p className="text-sm text-gray-500 text-center mt-4">
            + {pullRequests.length - 5} more PRs
          </p>
        )}
      </CardContent>
    </Card>
  );
};

const PRMetric = ({ label, value }) => (
  <div className="text-center">
    <p className="text-xl font-bold text-gray-900">{value}</p>
    <p className="text-xs text-gray-600">{label}</p>
  </div>
);

const CIStatusBadge = ({ status }) => {
  const statusConfig = {
    success: { text: '✓ Checks Passed', color: 'bg-green-100 text-green-800' },
    failure: { text: '✗ Checks Failed', color: 'bg-red-100 text-red-800' },
    pending: { text: '⏳ Checks Running', color: 'bg-yellow-100 text-yellow-800' }
  };
  const config = statusConfig[status] || statusConfig.pending;
  return (
    <span className={`text-xs px-2 py-1 rounded ${config.color}`}>
      {config.text}
    </span>
  );
};

export default PullRequestView;