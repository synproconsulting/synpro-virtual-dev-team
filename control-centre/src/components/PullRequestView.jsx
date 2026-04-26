import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { GitPullRequest, GitMerge, MessageSquare, CheckCircle, XCircle } from 'lucide-react';

const stateColors = {
  open: 'bg-green-100 text-green-800',
  merged: 'bg-purple-100 text-purple-800',
  closed: 'bg-red-100 text-red-800',
  draft: 'bg-gray-100 text-gray-800'
};

const reviewStatusIcons = {
  approved: <CheckCircle className="w-4 h-4 text-green-600" />,
  changes_requested: <XCircle className="w-4 h-4 text-red-600" />,
  pending: <MessageSquare className="w-4 h-4 text-yellow-600" />
};

const PullRequestView = ({ pullRequests = [], compact = false }) => {
  const renderPR = (pr) => (
    <div
      key={pr.id}
      className="flex items-start justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors"
    >
      <div className="flex-1 space-y-2">
        <div className="flex items-center gap-2">
          {pr.state === 'merged' ? (
            <GitMerge className="w-4 h-4 text-purple-600" />
          ) : (
            <GitPullRequest className="w-4 h-4 text-green-600" />
          )}
          <a
            href={pr.url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-blue-600 hover:underline"
          >
            {pr.title}
          </a>
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span>#{pr.number}</span>
          <span>by {pr.author}</span>
          <span>{pr.repository}</span>
        </div>
        <div className="flex items-center gap-3">
          {pr.reviewStatus && (
            <div className="flex items-center gap-1">
              {reviewStatusIcons[pr.reviewStatus]}
              <span className="text-xs">{pr.reviewsCount || 0} reviews</span>
            </div>
          )}
          {pr.ciStatus && (
            <div className="flex items-center gap-1">
              {pr.ciStatus === 'success' ? (
                <CheckCircle className="w-4 h-4 text-green-600" />
              ) : pr.ciStatus === 'failure' ? (
                <XCircle className="w-4 h-4 text-red-600" />
              ) : (
                <div className="w-4 h-4 border-2 border-yellow-600 border-t-transparent rounded-full animate-spin" />
              )}
              <span className="text-xs">CI</span>
            </div>
          )}
          <span className="text-xs text-gray-500">
            +{pr.additions || 0} -{pr.deletions || 0}
          </span>
        </div>
      </div>
      <Badge className={stateColors[pr.state] || 'bg-gray-100 text-gray-800'}>
        {pr.state}
      </Badge>
    </div>
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pull Requests {!compact && `(${pullRequests.length})`}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {pullRequests.map(renderPR)}
          {pullRequests.length === 0 && (
            <p className="text-center text-gray-500 py-4">No pull requests found</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default PullRequestView;