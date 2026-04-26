import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { CheckCircle, XCircle, Clock, PlayCircle } from 'lucide-react';

const statusConfig = {
  success: {
    icon: CheckCircle,
    color: 'text-green-600',
    badgeClass: 'bg-green-100 text-green-800'
  },
  failure: {
    icon: XCircle,
    color: 'text-red-600',
    badgeClass: 'bg-red-100 text-red-800'
  },
  running: {
    icon: PlayCircle,
    color: 'text-blue-600',
    badgeClass: 'bg-blue-100 text-blue-800'
  },
  pending: {
    icon: Clock,
    color: 'text-yellow-600',
    badgeClass: 'bg-yellow-100 text-yellow-800'
  }
};

const CIPipelineView = ({ pipelines = [], compact = false }) => {
  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const renderPipeline = (pipeline) => {
    const config = statusConfig[pipeline.status] || statusConfig.pending;
    const Icon = config.icon;

    return (
      <div
        key={pipeline.id}
        className="flex items-start justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors"
      >
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2">
            <Icon className={`w-5 h-5 ${config.color}`} />
            <a
              href={pipeline.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-blue-600 hover:underline"
            >
              {pipeline.name}
            </a>
          </div>
          <div className="flex items-center gap-3 text-xs text-gray-500">
            <span>{pipeline.repository}</span>
            <span>Branch: {pipeline.branch}</span>
            {pipeline.commit && (
              <span title={pipeline.commit}>
                {pipeline.commit.substring(0, 7)}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 text-xs text-gray-600">
            {pipeline.duration && (
              <span>Duration: {formatDuration(pipeline.duration)}</span>
            )}
            {pipeline.startedAt && (
              <span>Started: {new Date(pipeline.startedAt).toLocaleString()}</span>
            )}
          </div>
          {pipeline.stages && pipeline.stages.length > 0 && (
            <div className="flex gap-2 mt-2">
              {pipeline.stages.map((stage, idx) => {
                const stageConfig = statusConfig[stage.status] || statusConfig.pending;
                const StageIcon = stageConfig.icon;
                return (
                  <div
                    key={idx}
                    className="flex items-center gap-1 px-2 py-1 rounded text-xs border"
                    title={`${stage.name}: ${stage.status}`}
                  >
                    <StageIcon className={`w-3 h-3 ${stageConfig.color}`} />
                    <span>{stage.name}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
        <Badge className={config.badgeClass}>{pipeline.status}</Badge>
      </div>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>CI/CD Pipelines {!compact && `(${pipelines.length})`}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {pipelines.map(renderPipeline)}
          {pipelines.length === 0 && (
            <p className="text-center text-gray-500 py-4">No pipelines found</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default CIPipelineView;