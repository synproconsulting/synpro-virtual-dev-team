const API_URL = import.meta.env.VITE_API_URL || "";

export const login = async (email, password) => {
  const r = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    throw new Error(data.detail || `HTTP ${r.status}`);
  }
  return data;
};