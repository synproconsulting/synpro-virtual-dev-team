const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000';

/**
 * Trigger a SonarCloud analysis
 * @param {Object} config - Configuration for the analysis
 * @param {string} config.projectKey - SonarCloud project key
 * @param {string} config.branch - Branch to analyze
 * @param {string} config.pullRequest - Optional PR number
 * @returns {Promise<Object>} Response with task ID and dashboard URL
 */
export const triggerSonarAnalysis = async (config) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/sonarcloud/trigger`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error triggering SonarCloud analysis:', error);
    throw error;
  }
};

/**
 * Fetch SonarCloud analysis results
 * @param {string} projectKey - SonarCloud project key
 * @param {string} branch - Branch name (optional)
 * @returns {Promise<Object>} Analysis results including metrics and issues
 */
export const fetchSonarResults = async (projectKey, branch = 'main') => {
  try {
    const params = new URLSearchParams({
      projectKey,
      ...(branch && { branch }),
    });

    const response = await fetch(
      `${API_BASE_URL}/api/sonarcloud/results?${params.toString()}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching SonarCloud results:', error);
    throw error;
  }
};

/**
 * Fetch detailed issues from SonarCloud
 * @param {string} projectKey - SonarCloud project key
 * @param {string} branch - Branch name (optional)
 * @param {Object} filters - Filter options (types, severities, statuses)
 * @returns {Promise<Array>} Array of detailed issues
 */
export const fetchSonarIssues = async (projectKey, branch = 'main', filters = {}) => {
  try {
    const params = new URLSearchParams({
      projectKey,
      branch,
      ...(filters.types && { types: filters.types }),
      ...(filters.severities && { severities: filters.severities }),
      ...(filters.statuses && { statuses: filters.statuses }),
    });

    const response = await fetch(
      `${API_BASE_URL}/api/sonarcloud/issues?${params.toString()}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching SonarCloud issues:', error);
    throw error;
  }
};

/**
 * Get SonarCloud project metrics
 * @param {string} projectKey - SonarCloud project key
 * @param {string[]} metricKeys - Array of metric keys to fetch
 * @returns {Promise<Object>} Project metrics
 */
export const fetchSonarMetrics = async (projectKey, metricKeys = []) => {
  try {
    const params = new URLSearchParams({
      projectKey,
      ...(metricKeys.length > 0 && { metrics: metricKeys.join(',') }),
    });

    const response = await fetch(
      `${API_BASE_URL}/api/sonarcloud/metrics?${params.toString()}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching SonarCloud metrics:', error);
    throw error;
  }
};

/**
 * Get SonarCloud quality gate status
 * @param {string} projectKey - SonarCloud project key
 * @param {string} branch - Branch name (optional)
 * @returns {Promise<Object>} Quality gate status
 */
export const fetchQualityGateStatus = async (projectKey, branch = 'main') => {
  try {
    const params = new URLSearchParams({
      projectKey,
      ...(branch && { branch }),
    });

    const response = await fetch(
      `${API_BASE_URL}/api/sonarcloud/quality-gate?${params.toString()}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching quality gate status:', error);
    throw error;
  }
};
