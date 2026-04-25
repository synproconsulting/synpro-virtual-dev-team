import React from 'react';
import { Card, CardHeader, CardContent } from './ui/Card';
import { CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';

const BUILD_STATUS_CONFIG = {
  success: { color: 'text-green-600', bg: 'bg-green-50', icon: CheckCircle, label: 'Success' },
  failed: { color: 'text-red-600', bg: 'bg-red-50', icon: XCircle, label: 'Failed' },
  running: { color: 'text-blue-600', bg: 'bg-blue-50', icon: Clock, label: 'Running' },
  pending: { color: 'text-yellow-600', bg: 'bg-yellow-50', icon: Clock, label: 'Pending' },
  cancelled: { color: 'text-gray-600', bg: 'bg-gray-50', icon: AlertTriangle, label: 'Cancelled' },
};

const BuildCard = ({ build }) => {
  const config = BUILD_STATUS_CONFIG[build.status] || BUILD_STATUS_CONFIG.pending;
  const Icon = config.icon;

  return (
    <div className={`border rounded-lg p-4 ${config.bg}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <Icon className={`h-5 w-5 ${config.color}`} />
            <a
              href={build.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-lg font-semibold text-blue-600 hover:text-blue-800"
            >
              {build.jobName}
            </a>
          </div>
          <p className="text-sm text-gray-600 mt-1">
            Build #{build.buildNumber} • {build.branch}
          </p>
          <div className="flex items-center gap-4 mt-3">
            <span className={`text-sm font-medium ${config.color}`}>
              {config.label}
            </span>
            {build.duration && (
              <span className="text-sm text-gray-600">
                Duration: {Math.round(build.duration / 60)}m {build.duration % 60}s
              </span>
            )}
            <span className="text-sm text-gray-600">
              {new Date(build.timestamp).toLocaleString()}
            </span>
          </div>
          {build.commit && (
            <div className="mt-2 text-sm text-gray-600">
              <code className="bg-gray-200 px-2 py-1 rounded">{build.commit.substring(0, 7)}</code>
              <span className="ml-2">{build.commitMessage}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const CIIntegration = ({ sprintId, builds, onRefresh }) => {
  const successBuilds = builds?.filter(b => b.status === 'success').length || 0;
  const failedBuilds = builds?.filter(b => b.status === 'failed').length || 0;
  const runningBuilds = builds?.filter(b => b.status === 'running').length || 0;
  const totalBuilds = builds?.length || 0;

  const successRate = totalBuilds > 0
    ? Math.round((successBuilds / totalBuilds) * 100)
    : 0;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <h3 className="text-xl font-semibold">CI/CD Pipeline Status</h3>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-3xl font-bold text-blue-600">{successRate}%</p>
              <p className="text-sm text-gray-600">Success Rate</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-3xl font-bold text-green-600">{successBuilds}</p>
              <p className="text-sm text-gray-600">Successful</p>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <p className="text-3xl font-bold text-red-600">{failedBuilds}</p>
              <p className="text-sm text-gray-600">Failed</p>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <p className="text-3xl font-bold text-yellow-600">{runningBuilds}</p>
              <p className="text-sm text-gray-600">Running</p>
            </div>
          </div>

          <div className="space-y-3">
            {!builds || builds.length === 0 ? (
              <p className="text-gray-600 text-center py-8">No CI builds found for this sprint</p>
            ) : (
              builds.map((build) => <BuildCard key={build.id} build={build} />)
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CIIntegration;
