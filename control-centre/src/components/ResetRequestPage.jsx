import React, { useState } from "react";
import { requestPasswordReset, getErrorMessage } from "../api/authApi";

export default function ResetRequestPage({ onSwitchView }) {
  const [email, setEmail] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await requestPasswordReset(email);
      setResetToken(data.token || data.reset_token || "");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (resetToken) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <div className="auth-logo">
            <span className="cc-logo-icon">&#x26A1;</span>
            <span className="cc-logo-text">SynPro Control Centre</span>
          </div>
          <h2 className="auth-heading">Reset token generated</h2>
          <p className="auth-subtitle">UAT mode - token shown directly</p>
          <div className="auth-success">
            Password reset token created successfully.
          </div>
          <div className="auth-field">
            <label>Your reset token</label>
            <input type="text" value={resetToken} readOnly className="auth-mono" />
          </div>
          <p className="auth-hint">
            In production this would be emailed. For UAT, copy the token and use it on the next page.
          </p>
          <button
            className="auth-btn"
            onClick={() => onSwitchView("reset-complete", resetToken)}
          >
            Continue to set new password ?
          </button>
          <div className="auth-links">
            <button className="auth-link-btn" onClick={() => onSwitchView("login")}>
              Back to sign in
            </button>
          </div>
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
        <h2 className="auth-heading">Reset password</h2>
        <p className="auth-subtitle">Enter your email to get a reset token</p>
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-field">
            <label>Email address</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              autoFocus
            />
          </div>
          {error && <p className="auth-error">{error}</p>}
          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? "Sending." : "Get reset token"}
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