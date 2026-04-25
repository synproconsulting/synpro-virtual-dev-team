import React, { useState } from 'react';
import { Card, CardHeader, CardContent } from './ui/Card';
import { ExternalLink, RefreshCw } from 'lucide-react';

const STATUS_COLORS = {
  'To Do': 'bg-gray-200 text-gray-800',
  'In Progress': 'bg-blue-200 text-blue-800',
  'In Review': 'bg-purple-200 text-purple-800',
  'Done': 'bg-green-200 text-green-800',
  'Blocked': 'bg-red-200 text-red-800',
};

const PRIORITY_COLORS = {
  'Highest': 'text-red-600',
  'High': 'text-orange-600',
  'Medium': 'text-yellow-600',
  'Low': 'text-blue-600',
  'Lowest': 'text-gray-600',
};

const JiraIssueRow = ({ issue }) => (
  <tr className="border-b hover:bg-gray-50">
    <td className="px-4 py-3">
      <a
        href={issue.url}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center text-blue-600 hover:text-blue-800 font-medium"
      >
        {issue.key}
        <ExternalLink className="ml-1 h-3 w-3" />
      </a>
    </td>
    <td className="px-4 py-3">{issue.summary}</td>
    <td className="px-4 py-3">
      <span className={`text-sm font-semibold ${PRIORITY_COLORS[issue.priority] || 'text-gray-600'}`}>
        {issue.priority}
      </span>
    </td>
    <td className="px-4 py-3">
      <span className={`px-2 py-1 rounded text-xs font-medium ${STATUS_COLORS[issue.status] || 'bg-gray-200'}`}>
        {issue.status}
      </span>
    </td>
    <td className="px-4 py-3 text-sm text-gray-600">{issue.assignee}</td>
    <td className="px-4 py-3 text-sm text-gray-600">{issue.storyPoints || '-'}</td>
  </tr>
);

const JiraIntegration = ({ sprintId, issues, onRefresh }) => {
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    await onRefresh();
    setRefreshing(false);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-semibold">Jira Issues</h3>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </CardHeader>
      <CardContent>
        {!issues || issues.length === 0 ? (
          <p className="text-gray-600 text-center py-8">No issues found for this sprint</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Key</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Summary</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Priority</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Status</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Assignee</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Points</th>
                </tr>
              </thead>
              <tbody>
                {issues.map((issue) => (
                  <JiraIssueRow key={issue.key} issue={issue} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default JiraIntegration;
