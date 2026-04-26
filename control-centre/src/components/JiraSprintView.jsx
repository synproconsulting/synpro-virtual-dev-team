import React from 'react';
import { Card, CardHeader, CardContent } from './ui/Card';

const JiraSprintView = ({ data, compact = false }) => {
  if (!data) {
    return (
      <Card>
        <CardHeader>Jira Sprint Status</CardHeader>
        <CardContent>
          <p className="text-gray-500">No Jira data available</p>
        </CardContent>
      </Card>
    );
  }

  const { issues = [], summary = {} } = data;
  const statusColors = {
    'To Do': 'bg-gray-200 text-gray-800',
    'In Progress': 'bg-blue-200 text-blue-800',
    'In Review': 'bg-yellow-200 text-yellow-800',
    'Done': 'bg-green-200 text-green-800',
    'Blocked': 'bg-red-200 text-red-800'
  };

  const priorityIcons = {
    Highest: '🔴',
    High: '🟠',
    Medium: '🟡',
    Low: '🟢',
    Lowest: '⚪'
  };

  const displayIssues = compact ? issues.slice(0, 5) : issues;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Jira Sprint Status</h3>
          {summary.total > 0 && (
            <span className="text-sm text-gray-600">
              {summary.completed || 0} / {summary.total} completed
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {summary.total > 0 && (
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-gray-600">Sprint Progress</span>
              <span className="font-semibold">
                {Math.round((summary.completed / summary.total) * 100)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-blue-600 h-2.5 rounded-full transition-all"
                style={{ width: `${(summary.completed / summary.total) * 100}%` }}
              ></div>
            </div>
          </div>
        )}

        {!compact && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <StatusCount label="To Do" count={summary.todo || 0} />
            <StatusCount label="In Progress" count={summary.inProgress || 0} />
            <StatusCount label="In Review" count={summary.inReview || 0} />
            <StatusCount label="Done" count={summary.done || 0} />
          </div>
        )}

        <div className="space-y-3">
          {displayIssues.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No issues found</p>
          ) : (
            displayIssues.map((issue) => (
              <div
                key={issue.key}
                className="border rounded-lg p-3 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs">{priorityIcons[issue.priority]}</span>
                      <a
                        href={issue.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm font-medium text-blue-600 hover:underline"
                      >
                        {issue.key}
                      </a>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${statusColors[issue.status] || 'bg-gray-200'}`}
                      >
                        {issue.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-800">{issue.summary}</p>
                    {issue.assignee && (
                      <p className="text-xs text-gray-500 mt-1">
                        Assigned to: {issue.assignee}
                      </p>
                    )}
                  </div>
                  {issue.storyPoints && (
                    <div className="ml-2 text-sm font-semibold text-gray-600">
                      {issue.storyPoints} pts
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {compact && issues.length > 5 && (
          <p className="text-sm text-gray-500 text-center mt-4">
            + {issues.length - 5} more issues
          </p>
        )}
      </CardContent>
    </Card>
  );
};

const StatusCount = ({ label, count }) => (
  <div className="text-center">
    <p className="text-2xl font-bold text-gray-900">{count}</p>
    <p className="text-xs text-gray-600">{label}</p>
  </div>
);

export default JiraSprintView;