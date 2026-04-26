import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { ExternalLink } from 'lucide-react';

const statusColors = {
  'To Do': 'bg-gray-200 text-gray-800',
  'In Progress': 'bg-blue-200 text-blue-800',
  'In Review': 'bg-yellow-200 text-yellow-800',
  'Done': 'bg-green-200 text-green-800',
  'Blocked': 'bg-red-200 text-red-800'
};

const priorityColors = {
  'Highest': 'text-red-600',
  'High': 'text-orange-600',
  'Medium': 'text-yellow-600',
  'Low': 'text-blue-600',
  'Lowest': 'text-gray-600'
};

const JiraSprintView = ({ issues = [], compact = false }) => {
  const renderIssue = (issue) => (
    <div
      key={issue.key}
      className="flex items-start justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors"
    >
      <div className="flex-1 space-y-2">
        <div className="flex items-center gap-2">
          <a
            href={issue.url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-blue-600 hover:underline flex items-center gap-1"
          >
            {issue.key}
            <ExternalLink className="w-3 h-3" />
          </a>
          <Badge className={priorityColors[issue.priority] || 'text-gray-600'}>
            {issue.priority}
          </Badge>
        </div>
        <p className="text-sm text-gray-700">{issue.summary}</p>
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span>Assignee: {issue.assignee || 'Unassigned'}</span>
          {issue.storyPoints && <span>{issue.storyPoints} pts</span>}
        </div>
      </div>
      <Badge className={statusColors[issue.status] || 'bg-gray-200 text-gray-800'}>
        {issue.status}
      </Badge>
    </div>
  );

  const groupedIssues = issues.reduce((acc, issue) => {
    if (!acc[issue.status]) acc[issue.status] = [];
    acc[issue.status].push(issue);
    return acc;
  }, {});

  return (
    <Card>
      <CardHeader>
        <CardTitle>Jira Issues {!compact && `(${issues.length})`}</CardTitle>
      </CardHeader>
      <CardContent>
        {compact ? (
          <div className="space-y-2">
            {issues.map(renderIssue)}
            {issues.length === 0 && (
              <p className="text-center text-gray-500 py-4">No issues found</p>
            )}
          </div>
        ) : (
          <div className="space-y-6">
            {Object.entries(groupedIssues).map(([status, statusIssues]) => (
              <div key={status}>
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  {status}
                  <span className="text-sm text-gray-500">({statusIssues.length})</span>
                </h3>
                <div className="space-y-2">
                  {statusIssues.map(renderIssue)}
                </div>
              </div>
            ))}
            {issues.length === 0 && (
              <p className="text-center text-gray-500 py-8">No issues in this sprint</p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default JiraSprintView;