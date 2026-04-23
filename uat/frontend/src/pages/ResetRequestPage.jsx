import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { requestPasswordReset, getErrorMessage } from '../api'

export default function ResetRequestPage() {
  const [email,   setEmail]   = useState('')
  const [token,   setToken]   = useState('')
  const [error,   setError]   = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await requestPasswordReset(email)
      setToken(res.data.token)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  if (token) return (
    <div className="page">
      <div className="card">
        <h1>Reset token generated</h1>
        <p className="subtitle">UAT mode — token shown directly</p>
        <div className="success-box">
          Password reset token created successfully.
        </div>
        <div className="form-group">
          <label>Your reset token</label>
          <input type="text" value={token} readOnly
            style={{fontFamily:'monospace', fontSize:'0.8rem'}} />
        </div>
        <p style={{fontSize:'0.85rem', color:'var(--muted)', marginBottom:'1rem'}}>
          In production this would be emailed. For UAT, copy the token above and use it on the next page.
        </p>
        <Link to={`/reset-password/complete?token=${token}`}>
          <button className="btn">Continue to set new password →</button>
        </Link>
        <div className="link-row">
          <Link to="/login">Back to sign in</Link>
        </div>
      </div>
    </div>
  )

  return (
    <div className="page">
      <div className="card">
        <h1>Reset password</h1>
        <p className="subtitle">Enter your email to get a reset token</p>

        {error && <div className="error-box">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email address</label>
            <input type="email" value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com" required />
          </div>
          <button className="btn" type="submit" disabled={loading}>
            {loading ? 'Sending…' : 'Get reset token'}
          </button>
        </form>

        <div className="link-row">
          <Link to="/login">Back to sign in</Link>
        </div>
      </div>
    </div>
  )
}
