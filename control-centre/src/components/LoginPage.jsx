import React, { useState } from "react";
import { login } from "../api/authApi";

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login(email, password);
      onLogin(data.access_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-box">
        <div className="login-logo">
          <span className="cc-logo-icon">&#x26A1;</span>
          <span className="cc-logo-text">SynPro Control Centre</span>
        </div>
        <form onSubmit={handleSubmit} className="login-form">
          <div className="login-field">
            <label htmlFor="cc-email">Email</label>
            <input
              id="cc-email"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="login-field">
            <label htmlFor="cc-password">Password</label>
            <input
              id="cc-password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <p className="login-error">{error}</p>}
          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? "Logging in…" : "Login"}
          </button>
        </form>
      </div>
    </div>
  );
}