import React, { useState, useEffect, useCallback } from 'react';
import { AlertCircle, CheckCircle, Clock, XCircle, RefreshCw, GitBranch } from 'lucide-react';
import { fetchGitHubWorkflows, fetchWorkflowRuns } from '../api/github';

const STATUS_ICONS = {
  success: <CheckCircle className="w-5 h-5 text-green-500" />,
  failure: <XCircle className="w-5 h-5 text-red-500" />,
  in_progress: <Clock className="w-5 h-5 text-blue-500 animate-spin" />,
  queued: <Clock className="w-5 h-5 text-yellow-500" />,
  cancelled: <AlertCircle className="w-5 h-5 text-gray-500" />
};

const STATUS_COLORS = {
  success: 'bg-green-50 border-green-200',
  failure: 'bg-red-50 border-red-200',
  in_progress: 'bg-blue-50 border-blue-200',
  queued: 'bg-yellow-50 border-yellow-200',
  cancelled: 'bg-gray-50 border-gray-200'
};

export default function GitHubWorkflowMonitor({ repository, refreshInterval = 30000 }) {
  const [workflows, setWorkflows] = useState([]);
  const [runs, setRuns] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadWorkflowData = useCallback(async () => {
    try {
      setError(null);
      const workflowData = await fetchGitHubWorkflows(repository);
      setWorkflows(workflowData);

      const runsData = {};
      for (const workflow of workflowData) {
        const workflowRuns = await fetchWorkflowRuns(repository, workflow.id, 5);
        runsData[workflow.id] = workflowRuns;
      }
      setRuns(runsData);
      setLastUpdated(new Date());
      setLoading(false);
    } catch (err) {
      setError(err.message || 'Failed to load workflow data');
      setLoading(false);
    }
  }, [repository]);

  useEffect(() => {
    loadWorkflowData();
  }, [loadWorkflowData]);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      loadWorkflowData();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, loadWorkflowData]);

  const handleManualRefresh = () => {
    setLoading(true);
    loadWorkflowData();
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };

  if (loading && workflows.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center">
          <RefreshCw className="w-6 h-6 animate-spin text-blue-500 mr-2" />
          <span className="text-gray-600">Loading workflows...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center text-red-600">
          <AlertCircle className="w-5 h-5 mr-2" />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">GitHub Actions Monitor</h2>
            <p className="text-sm text-gray-500 mt-1">{repository}</p>
          </div>
          <div className="flex items-center space-x-4">
            {lastUpdated && (
              <span className="text-sm text-gray-500">
                Updated {formatTimestamp(lastUpdated)}
              </span>
            )}
            <label className="flex items-center space-x-2 text-sm">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded border-gray-300"
              />
              <span className="text-gray-600">Auto-refresh</span>
            </label>
            <button
              onClick={handleManualRefresh}
              disabled={loading}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {workflows.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            No workflows found for this repository
          </div>
        ) : (
          workflows.map((workflow) => (
            <WorkflowCard
              key={workflow.id}
              workflow={workflow}
              runs={runs[workflow.id] || []}
              formatTimestamp={formatTimestamp}
            />
          ))
        )}
      </div>
    </div>
  );
}

function WorkflowCard({ workflow, runs, formatTimestamp }) {
  const latestRun = runs[0];
  const recentRuns = runs.slice(0, 5);

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <h3 className="font-semibold text-gray-900">{workflow.name}</h3>
            {latestRun && STATUS_ICONS[latestRun.status]}
          </div>
          <span className="text-sm text-gray-500">{workflow.path}</span>
        </div>
      </div>

      <div className="divide-y divide-gray-200">
        {recentRuns.length === 0 ? (
          <div className="px-4 py-6 text-center text-gray-500 text-sm">
            No recent runs
          </div>
        ) : (
          recentRuns.map((run) => (
            <WorkflowRun key={run.id} run={run} formatTimestamp={formatTimestamp} />
          ))
        )}
      </div>
    </div>
  );
}

function WorkflowRun({ run, formatTimestamp }) {
  const statusColor = STATUS_COLORS[run.status] || 'bg-gray-50 border-gray-200';

  return (
    <div className={`px-4 py-3 hover:bg-gray-50 transition-colors ${statusColor}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3 flex-1">
          {STATUS_ICONS[run.status]}
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2">
              <span className="font-medium text-gray-900 truncate">
                {run.name || run.head_commit?.message || 'Workflow run'}
              </span>
              <span className="text-xs text-gray-500">#{run.run_number}</span>
            </div>
            <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
              <span className="flex items-center space-x-1">
                <GitBranch className="w-3 h-3" />
                <span>{run.head_branch}</span>
              </span>
              <span>{run.actor?.login || 'Unknown'}</span>
              <span>{formatTimestamp(run.created_at)}</span>
            </div>
          </div>
        </div>
        <div className="ml-4">
          {run.html_url && (
            <a
              href={run.html_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:text-blue-700 text-sm font-medium"
            >
              View →
            </a>
          )}
        </div>
      </div>
    </div>
  );
}