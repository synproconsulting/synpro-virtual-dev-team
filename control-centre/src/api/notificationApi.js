const API_URL = import.meta.env.VITE_API_URL || "";

const authHeaders = () => ({
  "Content-Type": "application/json",
  Authorization: `Bearer ${localStorage.getItem("token") || ""}`,
});

export const getNotifications = async (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  const url = `${API_URL}/notifications/${qs ? `?${qs}` : ""}`;
  const r = await fetch(url, { headers: authHeaders() });
  const data = await r.json().catch(() => []);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return data;
};

export const markAsRead = async (id) => {
  const r = await fetch(`${API_URL}/notifications/${id}/read`, {
    method: "PATCH",
    headers: authHeaders(),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return data;
};

export const markAllAsRead = async () => {
  const r = await fetch(`${API_URL}/notifications/mark-all-read`, {
    method: "POST",
    headers: authHeaders(),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return data;
};

export const deleteNotification = async (id) => {
  await fetch(`${API_URL}/notifications/${id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
};

export const getUnreadCount = async () => {
  const r = await fetch(`${API_URL}/notifications/unread/count`, {
    headers: authHeaders(),
  });
  const data = await r.json().catch(() => ({ count: 0 }));
  return data.count ?? 0;
};

export default { getNotifications, markAsRead, markAllAsRead, deleteNotification, getUnreadCount };