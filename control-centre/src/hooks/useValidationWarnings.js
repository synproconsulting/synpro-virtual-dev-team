/**
 * useValidationWarnings.js
 * ────────────────────────
 * React hook for fetching and managing PM Agent validation warnings
 */

import { useState, useEffect, useCallback } from 'react';
import { fetchValidationWarnings, fetchSprintValidationWarnings } from '../api/validationApi';

/**
 * Hook to fetch and manage validation warnings
 * @param {Object} options - Configuration options
 * @param {number|string} options.sprintId - Optional sprint ID to filter warnings
 * @param {boolean} options.autoRefresh - Whether to auto-refresh warnings
 * @param {number} options.refreshInterval - Auto-refresh interval in milliseconds
 * @returns {Object} Validation warnings state and control functions
 */
export const useValidationWarnings = ({
  sprintId = null,
  autoRefresh = false,
  refreshInterval = 300000, // 5 minutes default
} = {}) => {
  const [warnings, setWarnings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastFetch, setLastFetch] = useState(null);

  const fetchWarnings = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = sprintId
        ? await fetchSprintValidationWarnings(sprintId)
        : await fetchValidationWarnings();
      
      // Transform backend warnings to frontend format
      const formattedWarnings = data.map(w => ({
        id: w.issue_key || w.id,
        issue_key: w.issue_key,
        type: w.type || 'MISSING_EXECUTION_ORDER',
        message: w.message || w.warning,
        suggestion: w.suggestion,
        severity: w.severity || (w.type === 'MISSING_EXECUTION_ORDER' ? 'critical' : 'info'),
      }));

      setWarnings(formattedWarnings);
      setLastFetch(new Date());
    } catch (err) {
      console.error('Failed to fetch validation warnings:', err);
      setError(err.message);
      setWarnings([]);
    } finally {
      setLoading(false);
    }
  }, [sprintId]);

  const refresh = useCallback(() => {
    return fetchWarnings();
  }, [fetchWarnings]);

  // Initial fetch
  useEffect(() => {
    fetchWarnings();
  }, [fetchWarnings]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchWarnings();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchWarnings]);

  return {
    warnings,
    loading,
    error,
    lastFetch,
    refresh,
    hasWarnings: warnings.length > 0,
    criticalCount: warnings.filter(w => w.severity === 'critical').length,
    warningCount: warnings.filter(w => w.severity === 'warning').length,
    infoCount: warnings.filter(w => w.severity === 'info').length,
  };
};

export default useValidationWarnings;
