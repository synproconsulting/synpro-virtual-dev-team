import React, { useState } from 'react';
import {
  Box,
  Container,
  TextField,
  Button,
  Paper,
  Typography,
  Stack,
  Divider
} from '@mui/material';
import { Search } from '@mui/icons-material';
import GitHubWorkflowMonitor from './GitHubWorkflowMonitor';

const GitHubWorkflowDashboard = () => {
  const [repository, setRepository] = useState(
    process.env.REACT_APP_DEFAULT_GITHUB_REPO || ''
  );
  const [activeRepo, setActiveRepo] = useState(
    process.env.REACT_APP_DEFAULT_GITHUB_REPO || ''
  );
  const [pollingInterval, setPollingInterval] = useState(30000);

  const handleSearch = (e) => {
    e.preventDefault();
    if (repository.trim()) {
      setActiveRepo(repository.trim());
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          GitHub Actions Workflow Monitor
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Monitor GitHub Actions workflows in real-time with automatic updates every {pollingInterval / 1000} seconds.
        </Typography>
        
        <Divider sx={{ my: 2 }} />
        
        <Box component="form" onSubmit={handleSearch}>
          <Stack direction="row" spacing={2} alignItems="center">
            <TextField
              fullWidth
              label="Repository"
              placeholder="owner/repository"
              value={repository}
              onChange={(e) => setRepository(e.target.value)}
              helperText="Format: owner/repo (e.g., facebook/react)"
              variant="outlined"
              size="medium"
            />
            <TextField
              label="Polling (seconds)"
              type="number"
              value={pollingInterval / 1000}
              onChange={(e) => setPollingInterval(Math.max(10, parseInt(e.target.value) || 30) * 1000)}
              inputProps={{ min: 10, max: 300 }}
              sx={{ width: 180 }}
              variant="outlined"
              size="medium"
            />
            <Button
              type="submit"
              variant="contained"
              startIcon={<Search />}
              size="large"
              disabled={!repository.trim()}
            >
              Monitor
            </Button>
          </Stack>
        </Box>
      </Paper>

      {activeRepo ? (
        <GitHubWorkflowMonitor
          repository={activeRepo}
          pollingInterval={pollingInterval}
        />
      ) : (
        <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            Enter a GitHub repository to start monitoring workflows
          </Typography>
        </Paper>
      )}
    </Container>
  );
};

export default GitHubWorkflowDashboard;