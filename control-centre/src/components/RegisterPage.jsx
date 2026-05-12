import React, { useState } from "react";
import { register, getErrorMessage } from "../api/authApi";

export default function RegisterPage({ onLogin, onSwitchView }) {
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
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
      const data = await register(email, password, username);
      onLogin(data.access_token);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <span className="cc-logo-icon">&#x26A1;</span>
          <span className="cc-logo-text">SynPro Control Centre</span>
        </div>
        <p className="auth-subtitle">Create your account</p>
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
          <div className="auth-field">
            <label>
              Username <span className="auth-optional">(optional)</span>
            </label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="yourname"
            />
          </div>
          <div className="auth-field">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Min 8 chars, upper, lower, number, symbol"
              required
            />
          </div>
          <div className="auth-field">
            <label>Confirm password</label>
            <input
              type="password"
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
              placeholder="Repeat your password"
              required
            />
          </div>
          {error && <p className="auth-error">{error}</p>}
          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? "Creating account." : "Create account"}
          </button>
        </form>
        <hr className="auth-divider" />
        <div className="auth-links">
          Already have an account?{" "}
          <button className="auth-link-btn" onClick={() => onSwitchView("login")}>
            Sign in
          </button>
        </div>
      </div>
    </div>
  );
}