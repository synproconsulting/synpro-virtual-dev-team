import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, CheckCircle, XCircle, AlertTriangle, Bug, Shield } from 'lucide-react';
import { fetchSonarResults, fetchAnalysisStatus } from '../../api/sonarcloud';

const SonarCloudResults = ({ projectKey, taskId }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);
  const [status, setStatus] = useState(null);

  useEffect(() => {
    if (projectKey) {
      loadResults();
    }
  }, [projectKey]);

  useEffect(() => {
    if (taskId) {
      pollAnalysisStatus();
    }
  }, [taskId]);

  const pollAnalysisStatus = async () => {
    try {
      const statusData = await fetchAnalysisStatus(taskId);
      setStatus(statusData);

      if (statusData.status === 'SUCCESS') {
        loadResults();
      } else if (statusData.status === 'PENDING' || statusData.status === 'IN_PROGRESS') {
        setTimeout(pollAnalysisStatus, 5000);
      }
    } catch (err) {
      console.error('Error polling status:', err);
    }
  };

  const loadResults = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await fetchSonarResults(projectKey);
      setResults(data);
    } catch (err) {
      setError(err.message || 'Failed to load SonarCloud results');
    } finally {
      setLoading(false);
    }
  };

  const getQualityGateColor = (status) => {
    switch (status) {
      case 'OK':
      case 'PASSED':
        return 'bg-green-500';
      case 'ERROR':
      case 'FAILED':
        return 'bg-red-500';
      case 'WARN':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'CRITICAL':
      case 'BLOCKER':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'MAJOR':
        return <AlertTriangle className="h-4 w-4 text-orange-600" />;
      default:
        return <Bug className="h-4 w-4 text-yellow-600" />;
    }
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full">
        <CardContent className="py-4">
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (!results) {
    return null;
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            SonarCloud Analysis Results
          </span>
          {status && (
            <Badge variant="outline" className="ml-2">
              {status.status}
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Quality Gate */}
        <div className="flex items-center gap-3">
          <div className={`h-3 w-3 rounded-full ${getQualityGateColor(results.qualityGateStatus)}`} />
          <span className="font-semibold">Quality Gate:</span>
          <span className="text-lg">{results.qualityGateStatus || 'N/A'}</span>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            label="Bugs"
            value={results.bugs || 0}
            icon={<Bug className="h-5 w-5 text-red-500" />}
          />
          <MetricCard
            label="Vulnerabilities"
            value={results.vulnerabilities || 0}
            icon={<Shield className="h-5 w-5 text-orange-500" />}
          />
          <MetricCard
            label="Code Smells"
            value={results.codeSmells || 0}
            icon={<AlertTriangle className="h-5 w-5 text-yellow-500" />}
          />
          <MetricCard
            label="Coverage"
            value={results.coverage ? `${results.coverage}%` : 'N/A'}
            icon={<CheckCircle className="h-5 w-5 text-green-500" />}
          />
        </div>

        {/* Issues List */}
        {results.issues && results.issues.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-semibold text-sm text-gray-700">Recent Issues</h4>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {results.issues.slice(0, 10).map((issue, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2 p-2 border rounded-lg hover:bg-gray-50"
                >
                  {getSeverityIcon(issue.severity)}
                  <div className="flex-1 text-sm">
                    <div className="font-medium">{issue.message}</div>
                    <div className="text-gray-500 text-xs">
                      {issue.component} • Line {issue.line}
                    </div>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {issue.severity}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const MetricCard = ({ label, value, icon }) => (
  <div className="border rounded-lg p-3 space-y-1">
    <div className="flex items-center gap-2">
      {icon}
      <span className="text-xs text-gray-600">{label}</span>
    </div>
    <div className="text-2xl font-bold">{value}</div>
  </div>
);

export default SonarCloudResults;
