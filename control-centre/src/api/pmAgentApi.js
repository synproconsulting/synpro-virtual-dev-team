const API_URL = import.meta.env.VITE_API_URL || "";

export const sendPMAgentMessage = async (message, conversationHistory = []) => {
  if (!API_URL) throw new Error("VITE_API_URL not configured");
  const r = await fetch(`${API_URL}/api/pm-agent/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history: conversationHistory }),
  });
  if (!r.ok) throw new Error(`PM Agent error: ${r.status}`);
  const data = await r.json();
  // Map backend 'reply' field to 'message' for component compatibility
  return {
    message:    data.reply || data.message || "",
    sprintPlan: data.plan  || data.sprintPlan || null,
    role:       data.role  || "assistant",
  };
};

export const generateSprintPlan = async (brief, conversationHistory = []) => {
  if (!API_URL) throw new Error("VITE_API_URL not configured");
  const r = await fetch(`${API_URL}/api/pm-agent/generate-sprint`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ brief, history: conversationHistory }),
  });
  if (!r.ok) throw new Error(`Sprint generation error: ${r.status}`);
  return r.json();
};

export const approveSprint = async (plan) => {
  // Sprint plan approved - could trigger PM Agent to create Jira tickets
  return { success: true, plan };
};

export const rejectSprint = async (plan, feedback) => {
  // Sprint plan rejected with feedback
  return { success: true, feedback };
};

// Aliases
export const sendPMMessage = sendPMAgentMessage;
