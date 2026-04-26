import React, { useState } from 'react';
import { Card, CardHeader, CardContent } from './ui/Card';

const CIStatusView = ({ data }) => {
  const [selectedPipeline, setSelectedPipeline] = useState(null);

  if (!data) {
    return (
      <Card>
        <CardHeader>CI/CD Status</CardHeader>
        <CardContent>
          <p className="text-gray-500">No CI/CD data available</p>
        </CardContent>
      </Card>
    );
  }

  const { pipelines = [], summary = {} } = data;

  const getStatusColor = (status) => {
    const colors = {
      success: 'bg-green-100 text-green-800 border-green-300',
      failure: 'bg-red-100 text-red-800 border-red-300',
      running: 'bg-blue-100 text-blue-800 border-blue-300',
      pending: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      cancelled: 'bg-gray-100 text-gray-800 border-gray-300'
    };
    return colors[status] || colors.pending;
  };

  const getStatusIcon = (status) => {
    const icons = {
      success: '✓',
      failure: '✗',
      running: '↻',
      pending: '⏳',
      cancelled: '⊘'
    };
    return icons[status] || '?';
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">CI/CD Overview</h3>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <CIMetric
              label="Success Rate"
              value={`${summary.successRate || 0}%`}
              color="text-green-600"
            />
            <CIMetric
              label="Running"
              value={summary.running || 0}
              color="text-blue-600"
            />
            <CIMetric
              label="Failed"
              value={summary.failed || 0}
              color="text-red-600"
            />
            <CIMetric
              label="Avg Duration"
              value={summary.avgDuration || 'N/A'}
              color="text-gray-600"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">Recent Pipeline Runs</h3>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {pipelines.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No pipeline runs found</p>
            ) : (
              pipelines.map((pipeline) => (
                <div
                  key={pipeline.id}
                  className="border rounded-lg p-4 hover:bg-gray-50 transition-colors cursor-pointer"
                  onClick={() => setSelectedPipeline(
                    selectedPipeline?.id === pipeline.id ? null : pipeline
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span
                          className={`text-sm px-3 py-1 rounded border font-medium ${getStatusColor(pipeline.status)}`}
                        >
                          {getStatusIcon(pipeline.status)} {pipeline.status}
                        </span>
                        {pipeline.branch && (
                          <span className="text-sm text-gray-600">
                            🌿 {pipeline.branch}
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-medium text-gray-900 mb-1">
                        {pipeline.name}
                      </p>
                      <div className="flex items-center gap-3 text-xs text-gray-600">
                        <span>#{pipeline.number}</span>
                        {pipeline.commit && (
                          <span title={pipeline.commit.message}>
                            {pipeline.commit.sha?.substring(0, 7)}
                          </span>
                        )}
                        <span>by {pipeline.triggeredBy}</span>
                        <span>{pipeline.startedAt}</span>
                      </div>
                    </div>
                    <div className="ml-4 text-right">
                      {pipeline.duration && (
                        <div className="text-sm font-medium text-gray-900">
                          {pipeline.duration}
                        </div>
                      )}
                      <a
                        href={pipeline.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        View Details →
                      </a>
                    </div>
                  </div>

                  {selectedPipeline?.id === pipeline.id && pipeline.jobs && (
                    <div className="mt-4 pt-4 border-t">
                      <p className="text-sm font-medium text-gray-700 mb-2">Jobs:</p>
                      <div className="space-y-2">
                        {pipeline.jobs.map((job, idx) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between text-sm bg-gray-50 p-2 rounded"
                          >
                            <div className="flex items-center gap-2">
                              <span>{getStatusIcon(job.status)}</span>
                              <span className="font-medium">{job.name}</span>
                            </div>
                            <span className="text-gray-600">{job.duration}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const CIMetric = ({ label, value, color }) => (
  <div className="text-center">
    <p className={`text-2xl font-bold ${color}`}>{value}</p>
    <p className="text-xs text-gray-600 mt-1">{label}</p>
  </div>
);

export default CIStatusView;