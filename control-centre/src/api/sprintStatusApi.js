/**
 * sprintStatusApi.js
 * ==================
 * API client for sprint status endpoints
 */

const API_URL = import.meta.env.VITE_API_URL || "";

/**
 * Fetch current sprint status with comprehensive metrics
 * @returns {Promise<Object>} Current sprint status data
 */
export const fetchCurrentSprintStatus = async () => {
  if (!API_URL) {
    console.warn("VITE_API_URL not configured");
    return null;
  }

  try {
    const response = await fetch(`${API_URL}/api/sprint-status/current`);
    if (!response.ok) {
      console.error(`Sprint status API returned ${response.status}`);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching sprint status:", error);
    return null;
  }
};

/**
 * Check sprint status service health
 * @returns {Promise<Object>} Health check data
 */
export const checkSprintStatusHealth = async () => {
  if (!API_URL) {
    return { status: "error", message: "API_URL not configured" };
  }

  try {
    const response = await fetch(`${API_URL}/api/sprint-status/health-check`);
    if (!response.ok) {
      return { status: "error", message: `HTTP ${response.status}` };
    }
    return await response.json();
  } catch (error) {
    return { status: "error", message: error.message };
  }
};
