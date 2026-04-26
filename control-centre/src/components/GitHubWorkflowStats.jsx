import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle, XCircle, Clock, TrendingUp } from 'lucide-react';
import { getWorkflowSummary } from '../api/github';

export default function GitHubWorkflowStats({ repository }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadStats = async () => {
      try {
        setLoading(true);
        const summary = await getWorkflowSummary(repository);
        
        const successCount = summary.recentRuns.filter(r => r.status === 'success').length;
        const failureCount = summary.recentRuns.filter(r => r.status === 'failure').length;
        const inProgressCount = summary.recentRuns.filter(r => r.status === 'in_progress').length;
        
        const successRate = summary.recentRuns.length > 0
          ? Math.round((successCount / summary.recentRuns.length) * 100)
          : 0;

        setStats({
          totalWorkflows: summary.total,
          activeWorkflows: summary.active,
          successCount,
          failureCount,
          inProgressCount,
          successRate
        });
        setError(null);
      } catch (err) {
        setError(err.message || 'Failed to load workflow stats');
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, [repository]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        Failed to load stats: {error}
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        title="Active Workflows"
        value={stats.activeWorkflows}
        subtitle={`of ${stats.totalWorkflows} total`}
        icon={<Activity className="w-6 h-6 text-blue-500" />}
        bgColor="bg-blue-50"
      />
      <StatCard
        title="Success Rate"
        value={`${stats.successRate}%`}
        subtitle="Last 10 runs"
        icon={<TrendingUp className="w-6 h-6 text-green-500" />}
        bgColor="bg-green-50"
      />
      <StatCard
        title="Successful"
        value={stats.successCount}
        subtitle="Recent runs"
        icon={<CheckCircle className="w-6 h-6 text-green-500" />}
        bgColor="bg-green-50"
      />
      <StatCard
        title="Failed"
        value={stats.failureCount}
        subtitle="Recent runs"
        icon={<XCircle className="w-6 h-6 text-red-500" />}
        bgColor="bg-red-50"
      />
    </div>
  );
}

function StatCard({ title, value, subtitle, icon, bgColor }) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        <div className={`p-2 rounded-lg ${bgColor}`}>
          {icon}
        </div>
      </div>
      <div className="space-y-1">
        <p className="text-3xl font-bold text-gray-900">{value}</p>
        <p className="text-xs text-gray-500">{subtitle}</p>
      </div>
    </div>
  );
}