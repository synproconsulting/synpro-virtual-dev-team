import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from './ui/Card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/Tabs';
import SprintMetrics from './SprintMetrics';
import JiraIntegration from './JiraIntegration';
import PRIntegration from './PRIntegration';
import CIIntegration from './CIIntegration';
import { fetchSprintStatus } from '../../api/sprint_status';

const SprintStatusDashboard = ({ sprintId }) => {
  const [sprintData, setSprintData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadSprintData();
    const interval = setInterval(loadSprintData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [sprintId]);

  const loadSprintData = async () => {
    try {
      setLoading(true);
      const data = await fetchSprintStatus(sprintId);
      setSprintData(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
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
          <p className="text-red-600">Error loading sprint data: {error}</p>
          <button
            onClick={loadSprintData}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <h2 className="text-2xl font-bold">Sprint Status - {sprintData?.name}</h2>
          <p className="text-gray-600">
            {sprintData?.startDate} - {sprintData?.endDate}
          </p>
        </CardHeader>
        <CardContent>
          <SprintMetrics metrics={sprintData?.metrics} />
        </CardContent>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="prs">Pull Requests</TabsTrigger>
          <TabsTrigger value="ci">CI/CD Status</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <JiraIntegration
            sprintId={sprintId}
            issues={sprintData?.jiraIssues}
            onRefresh={loadSprintData}
          />
        </TabsContent>

        <TabsContent value="prs" className="space-y-4">
          <PRIntegration
            sprintId={sprintId}
            pullRequests={sprintData?.pullRequests}
            onRefresh={loadSprintData}
          />
        </TabsContent>

        <TabsContent value="ci" className="space-y-4">
          <CIIntegration
            sprintId={sprintId}
            builds={sprintData?.ciBuilds}
            onRefresh={loadSprintData}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SprintStatusDashboard;
