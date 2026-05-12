import React, { useEffect, useState } from "react";
import { getNotifications, markAsRead, markAllAsRead } from "../api/notificationApi";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = () => {
    setLoading(true);
    getNotifications()
      .then(setNotifications)
      .catch(err => setError(err.message || "Failed to load notifications"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleMarkRead = async (id) => {
    try {
      await markAsRead(id);
      setNotifications(prev =>
        prev.map(n => n.id === id ? { ...n, read: true } : n)
      );
    } catch {}
  };

  const handleMarkAll = async () => {
    try {
      await markAllAsRead();
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    } catch {}
  };

  if (loading) return <div className="notif-page-loading">Loading notifications.</div>;

  return (
    <div className="notif-page">
      <div className="notif-page-header">
        <h2>Notifications</h2>
        {notifications.some(n => !n.read) && (
          <button className="btn-primary" onClick={handleMarkAll}>Mark all read</button>
        )}
      </div>
      {error && <div className="notif-page-error">{error}</div>}
      {notifications.length === 0 ? (
        <div className="notif-page-empty">No notifications.</div>
      ) : (
        <div className="notif-list">
          {notifications.map(n => (
            <div key={n.id} className={`notif-item${n.read ? " notif-read" : ""}`}>
              <div className="notif-item-content">
                <p className="notif-item-message">{n.message || n.title || "Notification"}</p>
                {n.created_at && (
                  <span className="notif-item-time">
                    {new Date(n.created_at).toLocaleString()}
                  </span>
                )}
              </div>
              {!n.read && (
                <button className="notif-mark-read" onClick={() => handleMarkRead(n.id)}>
                  Mark read
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}