import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Loader2, RefreshCw, AlertTriangle, Bug, Code, ShieldAlert, TrendingUp } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const SonarCloudResults = ({ repository, autoRefresh = false }) => {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchResults = async () => {
    if (!repository) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/sonarcloud/results?repository=${encodeURIComponent(repository)}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch results');
      }

      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
  }, [repository]);

  useEffect(() => {
    if (autoRefresh && repository) {
      const interval = setInterval(fetchResults, 30000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, repository]);

  const getQualityGateColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'ok':
      case 'passed':
        return 'bg-green-500';
      case 'error':
      case 'failed':
        return 'bg-red-500';
      default:
        return 'bg-yellow-500';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'blocker':
      case 'critical':
        return <ShieldAlert className="h-4 w-4 text-red-600" />;
      case 'major':
        return <AlertTriangle className="h-4 w-4 text-orange-500" />;
      case 'minor':
        return <Bug className="h-4 w-4 text-yellow-500" />;
      default:
        return <Code className="h-4 w-4 text-blue-500" />;
    }
  };

  if (!repository) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-center text-muted-foreground">Select a repository to view results</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            SonarCloud Results
          </CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchResults}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading && !results ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        ) : error ? (
          <div className="text-center text-red-500 py-8">{error}</div>
        ) : results ? (
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="issues">Issues</TabsTrigger>
              <TabsTrigger value="metrics">Metrics</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="font-semibold">Quality Gate:</span>
                <Badge className={getQualityGateColor(results.qualityGate?.status)}>
                  {results.qualityGate?.status || 'Unknown'}
                </Badge>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground">Bugs</div>
                  <div className="text-2xl font-bold">{results.bugs || 0}</div>
                </div>
                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground">Vulnerabilities</div>
                  <div className="text-2xl font-bold">{results.vulnerabilities || 0}</div>
                </div>
                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground">Code Smells</div>
                  <div className="text-2xl font-bold">{results.codeSmells || 0}</div>
                </div>
                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground">Coverage</div>
                  <div className="text-2xl font-bold">{results.coverage || 0}%</div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="issues" className="space-y-3">
              {results.issues && results.issues.length > 0 ? (
                results.issues.map((issue, idx) => (
                  <div key={idx} className="border rounded-lg p-3 space-y-2">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        {getSeverityIcon(issue.severity)}
                        <span className="font-medium">{issue.severity}</span>
                      </div>
                      <Badge variant="outline">{issue.type}</Badge>
                    </div>
                    <p className="text-sm">{issue.message}</p>
                    <p className="text-xs text-muted-foreground">{issue.component}</p>
                  </div>
                ))
              ) : (
                <p className="text-center text-muted-foreground py-4">No issues found</p>
              )}
            </TabsContent>

            <TabsContent value="metrics" className="space-y-4">
              {results.metrics && Object.entries(results.metrics).map(([key, value]) => (
                <div key={key} className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="capitalize">{key.replace(/_/g, ' ')}</span>
                    <span className="font-semibold">{value}%</span>
                  </div>
                  <Progress value={parseFloat(value)} className="h-2" />
                </div>
              ))}
            </TabsContent>
          </Tabs>
        ) : null}
      </CardContent>
    </Card>
  );
};

export default SonarCloudResults;
