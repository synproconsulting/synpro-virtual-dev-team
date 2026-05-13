const API_URL = import.meta.env.VITE_API_URL || "";

const authHeader = () => ({
  "Content-Type": "application/json",
  Authorization: `Bearer ${localStorage.getItem("token") || ""}`,
});

export const getUserProfile = async () => {
  const r = await fetch(`${API_URL}/auth/me`, { headers: authHeader() });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || data.message || `HTTP ${r.status}`);
  return {
    ...data,
    name: data.username,
    createdAt: data.created_at,
  };
};

export const updateUserProfile = async (profileData) => {
  const r = await fetch(`${API_URL}/profile`, {
    method: "PUT",
    headers: authHeader(),
    body: JSON.stringify(profileData),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || data.message || `HTTP ${r.status}`);
  return data;
};
