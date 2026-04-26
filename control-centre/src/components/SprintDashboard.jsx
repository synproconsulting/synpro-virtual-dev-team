import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { fetchSprintData } from '../api/sprintApi';
import JiraSprintView from './JiraSprintView';
import PullRequestView from './PullRequestView';
import CIPipelineView from './CIPipelineView';
import SprintMetrics from './SprintMetrics';

const SprintDashboard = ({ sprintId }) => {
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
      const data = await fetchSprintData(sprintId);
      setSprintData(data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load sprint data');
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
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">
            Sprint Dashboard: {sprintData?.name || 'Loading...'}
          </CardTitle>
          <div className="text-sm text-gray-500">
            {sprintData?.startDate} - {sprintData?.endDate}
          </div>
        </CardHeader>
      </Card>

      <SprintMetrics metrics={sprintData?.metrics} />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="jira">Jira Issues</TabsTrigger>
          <TabsTrigger value="prs">Pull Requests</TabsTrigger>
          <TabsTrigger value="ci">CI/CD</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <JiraSprintView issues={sprintData?.jiraIssues?.slice(0, 5)} compact />
            <PullRequestView pullRequests={sprintData?.pullRequests?.slice(0, 5)} compact />
          </div>
          <CIPipelineView pipelines={sprintData?.ciPipelines?.slice(0, 3)} compact />
        </TabsContent>

        <TabsContent value="jira">
          <JiraSprintView issues={sprintData?.jiraIssues} />
        </TabsContent>

        <TabsContent value="prs">
          <PullRequestView pullRequests={sprintData?.pullRequests} />
        </TabsContent>

        <TabsContent value="ci">
          <CIPipelineView pipelines={sprintData?.ciPipelines} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SprintDashboard;