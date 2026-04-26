import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Grid,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
  Stack,
  LinearProgress
} from '@mui/material';
import {
  CheckCircle,
  Error,
  Schedule,
  Refresh,
  PlayArrow,
  Link as LinkIcon
} from '@mui/icons-material';
import { fetchGitHubWorkflows } from '../api/githubApi';

const GitHubWorkflowMonitor = ({ repository, pollingInterval = 30000 }) => {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const loadWorkflows = async () => {
    try {
      setError(null);
      const data = await fetchGitHubWorkflows(repository);
      setWorkflows(data);
      setLastUpdate(new Date());
    } catch (err) {
      setError(err.message || 'Failed to fetch workflows');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWorkflows();
    const interval = setInterval(loadWorkflows, pollingInterval);
    return () => clearInterval(interval);
  }, [repository, pollingInterval]);

  const getStatusIcon = (status, conclusion) => {
    if (status === 'in_progress' || status === 'queued') {
      return <Schedule color="warning" />;
    }
    if (conclusion === 'success') {
      return <CheckCircle color="success" />;
    }
    if (conclusion === 'failure') {
      return <Error color="error" />;
    }
    return <PlayArrow color="action" />;
  };

  const getStatusColor = (status, conclusion) => {
    if (status === 'in_progress' || status === 'queued') return 'warning';
    if (conclusion === 'success') return 'success';
    if (conclusion === 'failure') return 'error';
    return 'default';
  };

  const getStatusLabel = (status, conclusion) => {
    if (status === 'in_progress') return 'Running';
    if (status === 'queued') return 'Queued';
    if (conclusion === 'success') return 'Success';
    if (conclusion === 'failure') return 'Failed';
    if (conclusion === 'cancelled') return 'Cancelled';
    return status;
  };

  const formatDuration = (startTime, endTime) => {
    if (!startTime) return 'N/A';
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const diffMs = end - start;
    const minutes = Math.floor(diffMs / 60000);
    const seconds = Math.floor((diffMs % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
  };

  if (loading && workflows.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" component="h2">
          GitHub Actions Monitor
        </Typography>
        <Stack direction="row" spacing={1} alignItems="center">
          {lastUpdate && (
            <Typography variant="caption" color="text.secondary">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </Typography>
          )}
          <Tooltip title="Refresh">
            <IconButton onClick={loadWorkflows} size="small" disabled={loading}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Stack>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={2}>
        {workflows.map((workflow) => (
          <Grid item xs={12} md={6} lg={4} key={workflow.id}>
            <Card>
              <CardContent>
                <Stack spacing={2}>
                  <Box display="flex" justifyContent="space-between" alignItems="start">
                    <Box display="flex" alignItems="center" gap={1}>
                      {getStatusIcon(workflow.status, workflow.conclusion)}
                      <Typography variant="h6" component="div" noWrap>
                        {workflow.name}
                      </Typography>
                    </Box>
                    <Tooltip title="View on GitHub">
                      <IconButton
                        size="small"
                        href={workflow.html_url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <LinkIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>

                  <Box>
                    <Chip
                      label={getStatusLabel(workflow.status, workflow.conclusion)}
                      color={getStatusColor(workflow.status, workflow.conclusion)}
                      size="small"
                    />
                  </Box>

                  {workflow.status === 'in_progress' && (
                    <LinearProgress color="primary" />
                  )}

                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Branch: <strong>{workflow.head_branch}</strong>
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Event: {workflow.event}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Duration: {formatDuration(workflow.created_at, workflow.updated_at)}
                    </Typography>
                    {workflow.actor && (
                      <Typography variant="body2" color="text.secondary">
                        Triggered by: {workflow.actor.login}
                      </Typography>
                    )}
                  </Box>

                  {workflow.head_commit && (
                    <Typography variant="caption" color="text.secondary" noWrap>
                      {workflow.head_commit.message}
                    </Typography>
                  )}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {workflows.length === 0 && !loading && !error && (
        <Alert severity="info">
          No workflow runs found for this repository.
        </Alert>
      )}
    </Box>
  );
};

export default GitHubWorkflowMonitor;