import React from 'react';
import { CheckCircle, Clock, AlertCircle, TrendingUp } from 'lucide-react';

const MetricCard = ({ title, value, icon: Icon, trend, color }) => (
  <div className="bg-white p-4 rounded-lg border shadow-sm">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-gray-600">{title}</p>
        <p className="text-2xl font-bold mt-1">{value}</p>
        {trend && (
          <p className={`text-xs mt-1 ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend > 0 ? '+' : ''}{trend}% from last sprint
          </p>
        )}
      </div>
      <Icon className={`h-8 w-8 ${color}`} />
    </div>
  </div>
);

const SprintMetrics = ({ metrics }) => {
  if (!metrics) return null;

  const completionRate = metrics.totalIssues > 0
    ? Math.round((metrics.completedIssues / metrics.totalIssues) * 100)
    : 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricCard
        title="Completion Rate"
        value={`${completionRate}%`}
        icon={TrendingUp}
        trend={metrics.completionTrend}
        color="text-blue-600"
      />
      <MetricCard
        title="Completed Issues"
        value={`${metrics.completedIssues}/${metrics.totalIssues}`}
        icon={CheckCircle}
        color="text-green-600"
      />
      <MetricCard
        title="In Progress"
        value={metrics.inProgressIssues}
        icon={Clock}
        color="text-yellow-600"
      />
      <MetricCard
        title="Blocked Issues"
        value={metrics.blockedIssues}
        icon={AlertCircle}
        color="text-red-600"
      />
    </div>
  );
};

export default SprintMetrics;
