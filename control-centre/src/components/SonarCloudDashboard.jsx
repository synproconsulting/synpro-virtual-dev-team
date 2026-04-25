import React, { useState } from 'react';
import SonarCloudTrigger from './SonarCloudTrigger';
import SonarCloudResults from './SonarCloudResults';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Activity } from 'lucide-react';

const SonarCloudDashboard = () => {
  const [projectKey, setProjectKey] = useState('');
  const [branch, setBranch] = useState('main');
  const [taskId, setTaskId] = useState(null);

  const handleAnalysisTriggered = (result) => {
    setTaskId(result.taskId);
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-6 w-6" />
            SonarCloud Analysis Dashboard
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="space-y-2">
              <Label htmlFor="projectKey">Project Key</Label>
              <Input
                id="projectKey"
                placeholder="e.g., my-org_my-project"
                value={projectKey}
                onChange={(e) => setProjectKey(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="branch">Branch</Label>
              <Input
                id="branch"
                placeholder="e.g., main"
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
              />
            </div>
          </div>

          <Tabs defaultValue="trigger" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="trigger">Trigger Analysis</TabsTrigger>
              <TabsTrigger value="results">View Results</TabsTrigger>
            </TabsList>
            <TabsContent value="trigger" className="mt-6">
              <SonarCloudTrigger
                projectKey={projectKey}
                branch={branch}
                onAnalysisTriggered={handleAnalysisTriggered}
              />
            </TabsContent>
            <TabsContent value="results" className="mt-6">
              <SonarCloudResults
                projectKey={projectKey}
                taskId={taskId}
              />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default SonarCloudDashboard;
