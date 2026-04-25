import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, PlayCircle, AlertCircle } from 'lucide-react';
import { triggerSonarAnalysis } from '../../api/sonarcloud';

const SonarCloudTrigger = ({ projectKey, branch = 'main', onAnalysisTriggered }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleTrigger = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await triggerSonarAnalysis(projectKey, branch);
      setSuccess(`Analysis triggered successfully. Task ID: ${result.taskId}`);
      if (onAnalysisTriggered) {
        onAnalysisTriggered(result);
      }
    } catch (err) {
      setError(err.message || 'Failed to trigger SonarCloud analysis');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <PlayCircle className="h-5 w-5" />
          Trigger SonarCloud Analysis
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-col gap-2">
          <div className="text-sm text-gray-600">
            <span className="font-semibold">Project:</span> {projectKey}
          </div>
          <div className="text-sm text-gray-600">
            <span className="font-semibold">Branch:</span> {branch}
          </div>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert className="bg-green-50 text-green-800 border-green-200">
            <AlertDescription>{success}</AlertDescription>
          </Alert>
        )}

        <Button
          onClick={handleTrigger}
          disabled={loading || !projectKey}
          className="w-full"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Triggering Analysis...
            </>
          ) : (
            'Trigger Analysis'
          )}
        </Button>
      </CardContent>
    </Card>
  );
};

export default SonarCloudTrigger;
