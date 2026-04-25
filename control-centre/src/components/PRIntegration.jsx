import React from 'react';
import { Card, CardHeader, CardContent } from './ui/Card';
import { GitPullRequest, CheckCircle, XCircle, Clock, MessageSquare } from 'lucide-react';

const PR_STATUS_CONFIG = {
  open: { color: 'text-green-600', bg: 'bg-green-50', icon: GitPullRequest },
  merged: { color: 'text-purple-600', bg: 'bg-purple-50', icon: CheckCircle },
  closed: { color: 'text-red-600', bg: 'bg-red-50', icon: XCircle },
};

const PRCard = ({ pr }) => {
  const config = PR_STATUS_CONFIG[pr.status] || PR_STATUS_CONFIG.open;
  const Icon = config.icon;

  return (
    <div className={`border rounded-lg p-4 ${config.bg} hover:shadow-md transition-shadow`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <Icon className={`h-5 w-5 ${config.color}`} />
            <a
              href={pr.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-lg font-semibold text-blue-600 hover:text-blue-800"
            >
              {pr.title}
            </a>
          </div>
          <p className="text-sm text-gray-600 mt-1">
            #{pr.number} opened by {pr.author} • {pr.repo}
          </p>
          <div className="flex items-center gap-4 mt-3">
            <span className="flex items-center text-sm text-gray-600">
              <MessageSquare className="h-4 w-4 mr-1" />
              {pr.comments} comments
            </span>
            <span className={`text-sm font-medium ${config.color}`}>
              {pr.status.toUpperCase()}
            </span>
            {pr.ciStatus && (
              <span className={`flex items-center text-sm ${
                pr.ciStatus === 'success' ? 'text-green-600' : 
                pr.ciStatus === 'pending' ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {pr.ciStatus === 'success' ? <CheckCircle className="h-4 w-4 mr-1" /> :
                 pr.ciStatus === 'pending' ? <Clock className="h-4 w-4 mr-1" /> :
                 <XCircle className="h-4 w-4 mr-1" />}
                CI {pr.ciStatus}
              </span>
            )}
          </div>
          {pr.labels && pr.labels.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {pr.labels.map((label, idx) => (
                <span key={idx} className="px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded">
                  {label}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const PRIntegration = ({ sprintId, pullRequests, onRefresh }) => {
  const openPRs = pullRequests?.filter(pr => pr.status === 'open') || [];
  const mergedPRs = pullRequests?.filter(pr => pr.status === 'merged') || [];
  const closedPRs = pullRequests?.filter(pr => pr.status === 'closed') || [];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <h3 className="text-xl font-semibold">Pull Requests Overview</h3>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-3xl font-bold text-green-600">{openPRs.length}</p>
              <p className="text-sm text-gray-600">Open PRs</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <p className="text-3xl font-bold text-purple-600">{mergedPRs.length}</p>
              <p className="text-sm text-gray-600">Merged PRs</p>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <p className="text-3xl font-bold text-red-600">{closedPRs.length}</p>
              <p className="text-sm text-gray-600">Closed PRs</p>
            </div>
          </div>

          <div className="space-y-3">
            {!pullRequests || pullRequests.length === 0 ? (
              <p className="text-gray-600 text-center py-8">No pull requests found for this sprint</p>
            ) : (
              pullRequests.map((pr) => <PRCard key={pr.id} pr={pr} />)
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PRIntegration;
