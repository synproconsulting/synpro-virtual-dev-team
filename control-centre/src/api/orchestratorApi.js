/**
 * orchestratorApi.js
 * ==================
 * API client for Orchestrator state persistence and resume endpoints.
 * 
 * Provides functions to:
 * - Start sprint execution
 * - Resume from saved state
 * - Pause/cancel execution
 * - Query execution status and progress
 * - List resumable states
 */

const API_URL = import.meta.env.VITE_API_URL || "";

/**
 * Get headers with authentication token if available
 */
const getHeaders = () => {
  const token = localStorage.getItem("auth_token");
  return {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
  };
};

/**
 * Start a new sprint execution
 * @param {number} sprintId - Jira sprint ID
 * @param {string} sprintName - Sprint name
 * @param {string} jiraProjectKey - Jira project key (e.g., 'SDT1')
 * @returns {Promise<Object>} - { state_id, sprint_id, sprint_name, status, message }
 */
export const startSprint = async (sprintId, sprintName, jiraProjectKey) => {
  if (!API_URL) {
    throw new Error("API_URL not configured");
  }

  try {
    const response = await fetch(`${API_URL}/api/orchestrator/start`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({
        sprint_id: sprintId,
        sprint_name: sprintName,
        jira_project_key: jiraProjectKey,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("startSprint error:", error);
    throw error;
  }
};

/**
 * Resume a paused or failed sprint execution
 * @param {string} stateId - UUID of the state to resume
 * @param {string} jiraProjectKey - Jira project key
 * @returns {Promise<Object>} - { message, state_id, status }
 */
export const resumeSprint = async (stateId, jiraProjectKey) => {
  if (!API_URL) {
    throw new Error("API_URL not configured");
  }

  try {
    const response = await fetch(`${API_URL}/api/orchestrator/resume`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({
        state_id: stateId,
        jira_project_key: jiraProjectKey,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("resumeSprint error:", error);
    throw error;
  }
};

/**
 * Pause a running sprint execution
 * @param {string} stateId - UUID of the state
 * @param {string} [reason] - Optional reason for pausing
 * @returns {Promise<Object>} - { message, state_id, status }
 */
export const pauseSprint = async (stateId, reason = null) => {
  if (!API_URL) {
    throw new Error("API_URL not configured");
  }

  try {
    const response = await fetch(`${API_URL}/api/orchestrator/pause`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({
        state_id: stateId,
        ...(reason ? { reason } : {}),
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("pauseSprint error:", error);
    throw error;
  }
};

/**
 * Cancel a sprint execution
 * @param {string} stateId - UUID of the state
 * @param {string} [reason] - Optional reason for cancellation
 * @returns {Promise<Object>} - { message, state_id, status }
 */
export const cancelSprint = async (stateId, reason = null) => {
  if (!API_URL) {
    throw new Error("API_URL not configured");
  }

  try {
    const response = await fetch(`${API_URL}/api/orchestrator/cancel`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({
        state_id: stateId,
        ...(reason ? { reason } : {}),
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("cancelSprint error:", error);
    throw error;
  }
};

/**
 * Get execution progress for a state
 * @param {string} stateId - UUID of the state
 * @returns {Promise<Object>} - Progress information
 */
export const getProgress = async (stateId) => {
  if (!API_URL) {
    throw new Error("API_URL not configured");
  }

  try {
    const response = await fetch(`${API_URL}/api/orchestrator/progress/${stateId}`, {
      method: "GET",
      headers: getHeaders(),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("getProgress error:", error);
    throw error;
  }
};

/**
 * Get full state details including ticket lists
 * @param {string} stateId - UUID of the state
 * @returns {Promise<Object>} - Full state object
 */
export const getState = async (stateId) => {
  if (!API_URL) {
    throw new Error("API_URL not configured");
  }

  try {
    const response = await fetch(`${API_URL}/api/orchestrator/state/${stateId}`, {
      method: "GET",
      headers: getHeaders(),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("getState error:", error);
    throw error;
  }
};

/**
 * List all resumable sprint executions (PAUSED or FAILED)
 * @returns {Promise<Object>} - { states: [...], count: number }
 */
export const listResumable = async () => {
  if (!API_URL) {
    throw new Error("API_URL not configured");
  }

  try {
    const response = await fetch(`${API_URL}/api/orchestrator/resumable`, {
      method: "GET",
      headers: getHeaders(),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("listResumable error:", error);
    throw error;
  }
};
