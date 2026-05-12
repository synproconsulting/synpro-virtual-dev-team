import React, { useState } from "react";
import { completePasswordReset, getErrorMessage } from "../api/authApi";

export default function ResetCompletePage({ onSwitchView, initialToken = "" }) {
  const [token, setToken] = useState(initialToken);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }
    setLoading(true);
    try {
      await completePasswordReset(token, password);
      setSuccess(true);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <div className="auth-logo">
            <span className="cc-logo-icon">&#x26A1;</span>
            <span className="cc-logo-text">SynPro Control Centre</span>
          </div>
          <h2 className="auth-heading">Password updated</h2>
          <p className="auth-subtitle">Your password has been changed successfully</p>
          <div className="auth-success">
            You can now sign in with your new password.
          </div>
          <button className="auth-btn" onClick={() => onSwitchView("login")}>
            Sign in ?
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <span className="cc-logo-icon">&#x26A1;</span>
          <span className="cc-logo-text">SynPro Control Centre</span>
        </div>
        <h2 className="auth-heading">Set new password</h2>
        <p className="auth-subtitle">Enter your reset token and new password</p>
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-field">
            <label>Reset token</label>
            <input
              type="text"
              value={token}
              onChange={e => setToken(e.target.value)}
              placeholder="Paste your reset token"
              required
              className="auth-mono"
            />
          </div>
          <div className="auth-field">
            <label>New password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Min 8 chars, upper, lower, number, symbol"
              required
            />
          </div>
          <div className="auth-field">
            <label>Confirm new password</label>
            <input
              type="password"
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
              placeholder="Repeat your new password"
              required
            />
          </div>
          {error && <p className="auth-error">{error}</p>}
          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? "Updating." : "Update password"}
          </button>
        </form>
        <div className="auth-links">
          <button className="auth-link-btn" onClick={() => onSwitchView("login")}>
            Back to sign in
          </button>
        </div>
      </div>
    </div>
  );
}