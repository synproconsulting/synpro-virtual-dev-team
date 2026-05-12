import React, { useEffect, useState } from "react";
import { getMe, getErrorMessage } from "../api/authApi";

export default function UserDashboardPage({ token }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getMe(token)
      .then(setUser)
      .catch(err => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) return <div className="user-dash-loading">Loading.</div>;

  return (
    <div className="user-dash">
      <h2 className="user-dash-title">Account Details</h2>
      {error && <div className="user-dash-error">{error}</div>}
      {user && (
        <div className="user-dash-cards">
          <div className="card user-dash-card">
            <h3>Account</h3>
            <div className="user-dash-row">
              <span className="user-dash-label">Email</span>
              <span className="user-dash-value">{user.email}</span>
            </div>
            <div className="user-dash-row">
              <span className="user-dash-label">Username</span>
              <span className="user-dash-value">{user.username || "-"}</span>
            </div>
            <div className="user-dash-row">
              <span className="user-dash-label">User ID</span>
              <span className="user-dash-value user-dash-mono">{user.id}</span>
            </div>
            <div className="user-dash-row">
              <span className="user-dash-label">Member since</span>
              <span className="user-dash-value">
                {new Date(user.created_at).toLocaleDateString("en-GB", {
                  day: "numeric", month: "long", year: "numeric",
                })}
              </span>
            </div>
            <div className="user-dash-row">
              <span className="user-dash-label">Status</span>
              <span className="user-dash-value">
                <span className="badge badge-success">Active</span>
              </span>
            </div>
          </div>
          <div className="card user-dash-card">
            <h3>Environment</h3>
            <div className="user-dash-row">
              <span className="user-dash-label">Environment</span>
              <span className="user-dash-value">
                <span className="badge badge-info">UAT</span>
              </span>
            </div>
            <div className="user-dash-row">
              <span className="user-dash-label">Auth method</span>
              <span className="user-dash-value">JWT Bearer Token</span>
            </div>
            <div className="user-dash-row">
              <span className="user-dash-label">Token expires</span>
              <span className="user-dash-value">24 hours</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}