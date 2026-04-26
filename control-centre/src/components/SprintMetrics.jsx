import React from 'react';
import { Card, CardContent } from './ui/card';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const MetricCard = ({ title, value, trend, icon: Icon, color }) => {
  const getTrendIcon = () => {
    if (trend > 0) return <TrendingUp className="w-4 h-4 text-green-600" />;
    if (trend < 0) return <TrendingDown className="w-4 h-4 text-red-600" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-3xl font-bold">{value}</p>
            {trend !== undefined && (
              <div className="flex items-center gap-1 text-sm">
                {getTrendIcon()}
                <span className={trend > 0 ? 'text-green-600' : trend < 0 ? 'text-red-600' : 'text-gray-400'}>
                  {Math.abs(trend)}%
                </span>
              </div>
            )}
          </div>
          {Icon && (
            <div className={`p-3 rounded-full ${color || 'bg-blue-100'}`}>
              <Icon className="w-6 h-6" />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

const SprintMetrics = ({ metrics = {} }) => {
  const {
    velocity = 0,
    completedStoryPoints = 0,
    totalStoryPoints = 0,
    completionRate = 0,
    openPRs = 0,
    mergedPRs = 0,
    ciSuccessRate = 0,
    blockedIssues = 0,
    velocityTrend = 0,
    prTrend = 0,
    ciTrend = 0
  } = metrics;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricCard
        title="Sprint Velocity"
        value={velocity}
        trend={velocityTrend}
        color="bg-blue-100"
      />
      <MetricCard
        title="Story Points"
        value={`${completedStoryPoints}/${totalStoryPoints}`}
        trend={completionRate}
        color="bg-green-100"
      />
      <MetricCard
        title="Pull Requests"
        value={`${openPRs} open / ${mergedPRs} merged`}
        trend={prTrend}
        color="bg-purple-100"
      />
      <MetricCard
        title="CI Success Rate"
        value={`${ciSuccessRate}%`}
        trend={ciTrend}
        color="bg-yellow-100"
      />
    </div>
  );
};

export default SprintMetrics;