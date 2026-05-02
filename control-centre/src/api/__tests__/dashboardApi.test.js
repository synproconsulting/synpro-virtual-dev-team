/**
 * Tests for Dashboard API
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { 
  fetchSystemStatus, 
  fetchDashboardMetrics, 
  fetchOverviewStats,
  fetchRecentActivity 
} from '../dashboardApi';

// Mock environment variables
const mockEnv = {
  VITE_API_URL: 'http://localhost:3000',
  VITE_GITHUB_REPO: 'synproconsulting/synpro-virtual-dev-team',
  VITE_GITHUB_TOKEN: 'test-token'
};

// Mock fetch globally
global.fetch = vi.fn();

describe('dashboardApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset environment
    import.meta.env = { ...mockEnv };
  });

  describe('fetchSystemStatus', () => {
    it('should return operational status when all services are healthy', async () => {
      // Mock successful responses
      global.fetch
        .mockResolvedValueOnce({ ok: true, json: async () => ({}) }) // GitHub
        .mockResolvedValueOnce({ ok: true, json: async () => ({}) }) // Jira
        .mockResolvedValueOnce({ ok: true, json: async () => ({}) }); // UAT

      const status = await fetchSystemStatus();

      expect(status.overall).toBe('operational');
      expect(status.services.github).toBe('operational');
      expect(status.services.jira).toBe('operational');
      expect(status.services.uat).toBe('operational');
      expect(status.lastChecked).toBeDefined();
    });

    it('should return degraded status when GitHub is down', async () => {
      global.fetch
        .mockResolvedValueOnce({ ok: false }) // GitHub fails
        .mockResolvedValueOnce({ ok: true, json: async () => ({}) }) // Jira
        .mockResolvedValueOnce({ ok: true, json: async () => ({}) }); // UAT

      const status = await fetchSystemStatus();

      expect(status.overall).toBe('degraded');
      expect(status.services.github).toBe('degraded');
    });

    it('should handle network errors gracefully', async () => {
      global.fetch.mockRejectedValue(new Error('Network error'));

      const status = await fetchSystemStatus();

      expect(status.overall).toBe('degraded');
    });
  });

  describe('fetchDashboardMetrics', () => {
    it('should fetch and aggregate metrics correctly', async () => {
      const mockSprints = {
        sprints: [
          { id: 1, state: 'active' },
          { id: 2, state: 'active' },
          { id: 3, state: 'closed' }
        ]
      };

      const mockPRs = [
        { number: 1, state: 'open' },
        { number: 2, state: 'open' },
        { number: 3, state: 'open' }
      ];

      const mockRuns = {
        workflow_runs: [
          { 
            id: 1, 
            status: 'in_progress', 
            name: 'CI',
            created_at: new Date().toISOString()
          },
          { 
            id: 2, 
            status: 'completed', 
            conclusion: 'success',
            name: 'Deploy to UAT',
            created_at: new Date().toISOString()
          }
        ]
      };

      global.fetch
        .mockResolvedValueOnce({ ok: true, json: async () => mockSprints }) // Sprints
        .mockResolvedValueOnce({ ok: true, json: async () => mockPRs })     // PRs
        .mockResolvedValueOnce({ ok: true, json: async () => mockRuns });   // Runs

      const metrics = await fetchDashboardMetrics();

      expect(metrics.activeSprints).toBe(2);
      expect(metrics.openPRs).toBe(3);
      expect(metrics.activeWorkflows).toBe(1);
      expect(metrics.todayDeploys).toBe(1);
      expect(metrics.recentActivity).toHaveLength(2);
    });

    it('should return empty metrics on error', async () => {
      global.fetch.mockRejectedValue(new Error('API error'));

      const metrics = await fetchDashboardMetrics();

      expect(metrics.activeSprints).toBe(0);
      expect(metrics.openPRs).toBe(0);
      expect(metrics.activeWorkflows).toBe(0);
      expect(metrics.todayDeploys).toBe(0);
    });
  });

  describe('fetchOverviewStats', () => {
    it('should fetch both status and metrics', async () => {
      // Mock all API calls
      global.fetch
        .mockResolvedValueOnce({ ok: true, json: async () => ({}) })  // GitHub status
        .mockResolvedValueOnce({ ok: true, json: async () => ({}) })  // Jira status
        .mockResolvedValueOnce({ ok: true, json: async () => ({}) })  // UAT status
        .mockResolvedValueOnce({ ok: true, json: async () => ({ sprints: [] }) }) // Sprints
        .mockResolvedValueOnce({ ok: true, json: async () => [] })    // PRs
        .mockResolvedValueOnce({ ok: true, json: async () => ({ workflow_runs: [] }) }); // Runs

      const stats = await fetchOverviewStats();

      expect(stats.status).toBeDefined();
      expect(stats.metrics).toBeDefined();
      expect(stats.timestamp).toBeDefined();
    });

    it('should return safe defaults on complete failure', async () => {
      global.fetch.mockRejectedValue(new Error('Complete failure'));

      const stats = await fetchOverviewStats();

      expect(stats.status.overall).toBe('unknown');
      expect(stats.metrics.activeSprints).toBe(0);
      expect(stats.timestamp).toBeDefined();
    });
  });

  describe('fetchRecentActivity', () => {
    it('should fetch and merge recent activity from workflows and PRs', async () => {
      const now = new Date();
      const earlier = new Date(now.getTime() - 3600000);

      const mockRuns = {
        workflow_runs: [
          {
            id: 1,
            name: 'CI Pipeline',
            status: 'completed',
            conclusion: 'success',
            created_at: now.toISOString(),
            html_url: 'https://github.com/run/1',
            actor: { login: 'user1' }
          }
        ]
      };

      const mockPRs = [
        {
          number: 42,
          title: 'Fix bug',
          state: 'open',
          merged_at: null,
          updated_at: earlier.toISOString(),
          html_url: 'https://github.com/pr/42',
          user: { login: 'user2' }
        }
      ];

      global.fetch
        .mockResolvedValueOnce({ ok: true, json: async () => mockRuns })
        .mockResolvedValueOnce({ ok: true, json: async () => mockPRs });

      const activity = await fetchRecentActivity(10);

      expect(activity).toHaveLength(2);
      expect(activity[0].type).toBe('workflow'); // Most recent first
      expect(activity[1].type).toBe('pull_request');
    });

    it('should limit results to specified count', async () => {
      const mockRuns = {
        workflow_runs: Array(20).fill(null).map((_, i) => ({
          id: i,
          name: `Run ${i}`,
          status: 'completed',
          created_at: new Date().toISOString(),
          html_url: `https://github.com/run/${i}`,
          actor: { login: 'user' }
        }))
      };

      const mockPRs = Array(20).fill(null).map((_, i) => ({
        number: i,
        title: `PR ${i}`,
        state: 'open',
        updated_at: new Date().toISOString(),
        html_url: `https://github.com/pr/${i}`,
        user: { login: 'user' }
      }));

      global.fetch
        .mockResolvedValueOnce({ ok: true, json: async () => mockRuns })
        .mockResolvedValueOnce({ ok: true, json: async () => mockPRs });

      const activity = await fetchRecentActivity(5);

      expect(activity).toHaveLength(5);
    });

    it('should handle fetch errors gracefully', async () => {
      global.fetch.mockRejectedValue(new Error('Network error'));

      const activity = await fetchRecentActivity();

      expect(activity).toEqual([]);
    });
  });
});
