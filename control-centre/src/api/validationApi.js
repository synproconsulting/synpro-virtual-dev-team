/**
 * validationApi.js
 * ────────────────
 * API client for PM Agent validation warnings
 */

const API_URL = import.meta.env.VITE_API_URL || "";

/**
 * Fetch validation warnings for stories in the current sprint
 * @returns {Promise<Array>} Array of validation warning objects
 */
export const fetchValidationWarnings = async () => {
  if (!API_URL) {
    console.warn("VITE_API_URL not configured");
    return [];
  }
  
  try {
    const r = await fetch(`${API_URL}/api/pm-agent/validation-warnings`);
    if (!r.ok) {
      console.error(`Validation warnings fetch failed: ${r.status}`);
      return [];
    }
    const data = await r.json();
    return data.warnings || [];
  } catch (e) {
    console.error("fetchValidationWarnings error:", e);
    return [];
  }
};

/**
 * Fetch validation warnings for a specific sprint
 * @param {number|string} sprintId - The sprint ID to validate
 * @returns {Promise<Array>} Array of validation warning objects
 */
export const fetchSprintValidationWarnings = async (sprintId) => {
  if (!API_URL) {
    console.warn("VITE_API_URL not configured");
    return [];
  }
  
  try {
    const r = await fetch(`${API_URL}/api/pm-agent/validation-warnings?sprint_id=${sprintId}`);
    if (!r.ok) {
      console.error(`Sprint validation warnings fetch failed: ${r.status}`);
      return [];
    }
    const data = await r.json();
    return data.warnings || [];
  } catch (e) {
    console.error("fetchSprintValidationWarnings error:", e);
    return [];
  }
};

/**
 * Check a specific issue for validation warnings
 * @param {string} issueKey - The Jira issue key (e.g., "SDT1-26")
 * @returns {Promise<Object>} Validation result with warnings array
 */
export const validateIssue = async (issueKey) => {
  if (!API_URL) {
    console.warn("VITE_API_URL not configured");
    return { warnings: [], valid: true };
  }
  
  try {
    const r = await fetch(`${API_URL}/api/pm-agent/validate-issue/${issueKey}`);
    if (!r.ok) {
      console.error(`Issue validation failed: ${r.status}`);
      return { warnings: [], valid: true };
    }
    const data = await r.json();
    return {
      warnings: data.warnings || [],
      valid: (data.warnings || []).length === 0,
      issue_key: data.issue_key || issueKey,
    };
  } catch (e) {
    console.error("validateIssue error:", e);
    return { warnings: [], valid: true };
  }
};
