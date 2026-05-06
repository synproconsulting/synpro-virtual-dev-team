/**
 * API client for orchestrator state management
 * Handles fetching, resuming, and clearing orchestrator state
 */

const API_URL = import.meta.env.VITE_API_URL || "";

/**
 * Fetch the current orchestrator state
 * @returns {Promise<Object>} Current state or null if no state exists
 */
export const fetchOrchestratorState = async () => {
  if (!API_URL) {
    console.warn("API_URL not configured");
    return null;
  }
  
  try {
    const response = await fetch(`${API_URL}/orchestrator/state`);
    if (!response.ok) {
      if (response.status === 404) {
        return null; // No state file exists
      }
      throw new Error(`Failed to fetch state: ${response.statusText}`);
    }
    const data = await response.json();
    return data.state || null;
  } catch (error) {
    console.error("Error fetching orchestrator state:", error);
    return null;
  }
};

/**
 * Resume orchestrator from saved state
 * @returns {Promise<Object>} Result of resume operation
 */
export const resumeOrchestrator = async () => {
  if (!API_URL) {
    throw new Error("API_URL not configured");
  }
  
  try {
    const response = await fetch(`${API_URL}/orchestrator/resume`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to resume: ${response.statusText}`);
    }
    
    const data = await response.json();
    return {
      success: true,
      message: data.message || "Orchestrator resumed successfully",
      ...data,
    };
  } catch (error) {
    console.error("Error resuming orchestrator:", error);
    return {
      success: false,
      message: error.message || "Failed to resume orchestrator",
    };
  }
};

/**
 * Clear the orchestrator state
 * @returns {Promise<Object>} Result of clear operation
 */
export const clearOrchestratorState = async () => {
  if (!API_URL) {
    throw new Error("API_URL not configured");
  }
  
  try {
    const response = await fetch(`${API_URL}/orchestrator/state`, {
      method: "DELETE",
    });
    
    if (!response.ok) {
      throw new Error(`Failed to clear state: ${response.statusText}`);
    }
    
    const data = await response.json();
    return {
      success: true,
      message: data.message || "State cleared successfully",
    };
  } catch (error) {
    console.error("Error clearing orchestrator state:", error);
    return {
      success: false,
      message: error.message || "Failed to clear state",
    };
  }
};

/**
 * Check if orchestrator is currently running
 * @returns {Promise<Object>} Status information
 */
export const checkOrchestratorStatus = async () => {
  if (!API_URL) {
    return { running: false, message: "API_URL not configured" };
  }
  
  try {
    const response = await fetch(`${API_URL}/orchestrator/status`);
    if (!response.ok) {
      return { running: false, message: "Failed to fetch status" };
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error checking orchestrator status:", error);
    return { running: false, message: error.message };
  }
};
