// Backend notification endpoints are not yet implemented â€” uat/backend/notifications.py
// is a stub router (SDT1-47 placeholder) with no handlers, and no other router exposes
// notification routes. Calls to /notifications/* therefore return 404. Until the backend
// is built, this client returns safe defaults so the Notifications page renders without
// 404 errors. Replace these stubs with real fetch calls once the backend endpoints exist.

export const getNotifications = async () => [];

export const markAsRead = async (id) => ({ id, read: true });

export const markAllAsRead = async () => ({ ok: true });

export const deleteNotification = async (id) => {};

export const getUnreadCount = async () => 0;

export default { getNotifications, markAsRead, markAllAsRead, deleteNotification, getUnreadCount };
