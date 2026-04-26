import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from './ui/Card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/Tabs';
import JiraSprintView from './JiraSprintView';
import PullRequestView from './PullRequestView';
import CIStatusView from './CIStatusView';
import { fetchSprintData } from '../api/sprintApi';

const SprintStatusDashboard = () => {
  const [sprintData, setSprintData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [refreshInterval, setRefreshInterval] = useState(null);

  const loadSprintData = async () => {
    try {
      setLoading(true);
      const data = await fetchSprintData();
      setSprintData(data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load sprint data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSprintData();
    const interval = setInterval(loadSprintData, 300000); // Refresh every 5 minutes
    setRefreshInterval(interval);
    return () => clearInterval(interval);
  }, []);

  const handleManualRefresh = () => {
    loadSprintData();
  };

  if (loading && !sprintData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="pt-6">
          <div className="text-red-800">
            <p className="font-semibold">Error loading sprint data</p>
            <p className="text-sm mt-1">{error}</p>
            <button
              onClick={handleManualRefresh}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Sprint Status Dashboard</h1>
          <p className="text-gray-600 mt-1">
            {sprintData?.sprint?.name || 'Current Sprint'}
          </p>
        </div>
        <button
          onClick={handleManualRefresh}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="jira">Jira Issues</TabsTrigger>
          <TabsTrigger value="prs">Pull Requests</TabsTrigger>
          <TabsTrigger value="ci">CI/CD Status</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <SprintMetricCard
              title="Sprint Progress"
              value={sprintData?.metrics?.completionRate || 0}
              suffix="%"
              icon="📊"
            />
            <SprintMetricCard
              title="Open PRs"
              value={sprintData?.prs?.open || 0}
              icon="🔀"
            />
            <SprintMetricCard
              title="CI Success Rate"
              value={sprintData?.ci?.successRate || 0}
              suffix="%"
              icon="✓"
            />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <JiraSprintView data={sprintData?.jira} compact />
            <PullRequestView data={sprintData?.prs} compact />
          </div>
        </TabsContent>

        <TabsContent value="jira">
          <JiraSprintView data={sprintData?.jira} />
        </TabsContent>

        <TabsContent value="prs">
          <PullRequestView data={sprintData?.prs} />
        </TabsContent>

        <TabsContent value="ci">
          <CIStatusView data={sprintData?.ci} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

const SprintMetricCard = ({ title, value, suffix = '', icon }) => (
  <Card>
    <CardContent className="pt-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">
            {value}{suffix}
          </p>
        </div>
        <div className="text-4xl">{icon}</div>
      </div>
    </CardContent>
  </Card>
);

export default SprintStatusDashboard;