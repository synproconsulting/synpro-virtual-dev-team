import React, { useEffect, useState } from 'react'
import { getMe, getErrorMessage } from '../api'

export default function DashboardPage({ user: initialUser, token, onLogout }) {
  const [user,    setUser]    = useState(initialUser)
  const [loading, setLoading] = useState(!initialUser)
  const [error,   setError]   = useState('')

  useEffect(() => {
    if (!initialUser && token) {
      getMe(token)
        .then(res => setUser(res.data))
        .catch(err => setError(getErrorMessage(err)))
        .finally(() => setLoading(false))
    }
  }, [initialUser, token])

  if (loading) return (
    <div className="page">
      <p style={{color: 'var(--muted)'}}>Loading…</p>
    </div>
  )

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>SynPro UAT Dashboard</h1>
        <button className="btn btn-ghost" style={{width:'auto', padding:'0.5rem 1.25rem'}}
          onClick={onLogout}>
          Sign out
        </button>
      </div>

      {error && <div className="error-box" style={{maxWidth:900,margin:'0 auto 1rem'}}>{error}</div>}

      {user && (
        <>
          <div className="info-card">
            <h2>Account Details</h2>
            <div className="info-row">
              <span className="label">Email</span>
              <span className="value">{user.email}</span>
            </div>
            <div className="info-row">
              <span className="label">Username</span>
              <span className="value">{user.username}</span>
            </div>
            <div className="info-row">
              <span className="label">User ID</span>
              <span className="value" style={{fontFamily:'monospace',fontSize:'0.8rem'}}>
                {user.id}
              </span>
            </div>
            <div className="info-row">
              <span className="label">Member since</span>
              <span className="value">
                {new Date(user.created_at).toLocaleDateString('en-GB', {
                  day: 'numeric', month: 'long', year: 'numeric'
                })}
              </span>
            </div>
            <div className="info-row">
              <span className="label">Account status</span>
              <span className="value">
                <span className="badge badge-green">Active</span>
              </span>
            </div>
          </div>

          <div className="info-card">
            <h2>UAT Environment</h2>
            <div className="info-row">
              <span className="label">Environment</span>
              <span className="value"><span className="badge badge-blue">UAT</span></span>
            </div>
            <div className="info-row">
              <span className="label">API version</span>
              <span className="value">1.0.0</span>
            </div>
            <div className="info-row">
              <span className="label">Auth method</span>
              <span className="value">JWT Bearer Token</span>
            </div>
            <div className="info-row">
              <span className="label">Token expires</span>
              <span className="value">24 hours</span>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
