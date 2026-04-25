import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, PlayCircle, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const SonarCloudTrigger = ({ onAnalysisTriggered }) => {
  const [repository, setRepository] = useState('');
  const [branch, setBranch] = useState('main');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleTrigger = async () => {
    if (!repository.trim()) {
      setError('Repository name is required');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const response = await fetch('/api/sonarcloud/trigger', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repository: repository.trim(),
          branch: branch.trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to trigger analysis');
      }

      setSuccess(true);
      if (onAnalysisTriggered) {
        onAnalysisTriggered(data);
      }

      setTimeout(() => {
        setSuccess(false);
        setRepository('');
        setBranch('main');
      }, 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <PlayCircle className="h-5 w-5" />
          Trigger SonarCloud Analysis
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="repository">Repository</Label>
          <Input
            id="repository"
            placeholder="owner/repo-name"
            value={repository}
            onChange={(e) => setRepository(e.target.value)}
            disabled={loading}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="branch">Branch</Label>
          <Input
            id="branch"
            placeholder="main"
            value={branch}
            onChange={(e) => setBranch(e.target.value)}
            disabled={loading}
          />
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert className="border-green-500 bg-green-50">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-600">
              Analysis triggered successfully!
            </AlertDescription>
          </Alert>
        )}

        <Button
          onClick={handleTrigger}
          disabled={loading}
          className="w-full"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Triggering...
            </>
          ) : (
            <>
              <PlayCircle className="mr-2 h-4 w-4" />
              Trigger Analysis
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
};

export default SonarCloudTrigger;
