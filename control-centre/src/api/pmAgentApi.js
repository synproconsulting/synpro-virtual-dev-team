const API_URL = import.meta.env.VITE_API_URL || "";

export const sendPMAgentMessage = async (message, conversationHistory = []) => {
  if (!API_URL) throw new Error("VITE_API_URL not configured");
  const r = await fetch(`${API_URL}/api/pm-agent/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history: conversationHistory }),
  });
  if (!r.ok) throw new Error(`PM Agent error: ${r.status}`);
  return r.json();
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
