import React, { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { completePasswordReset, getErrorMessage } from '../api'

export default function ResetCompletePage() {
  const [searchParams]           = useSearchParams()
  const [token,    setToken]     = useState(searchParams.get('token') || '')
  const [password, setPassword]  = useState('')
  const [confirm,  setConfirm]   = useState('')
  const [error,    setError]     = useState('')
  const [success,  setSuccess]   = useState(false)
  const [loading,  setLoading]   = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (password !== confirm) {
      setError('Passwords do not match')
      return
    }
    setLoading(true)
    try {
      await completePasswordReset(token, password)
      setSuccess(true)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  if (success) return (
    <div className="page">
      <div className="card">
        <h1>Password updated</h1>
        <p className="subtitle">Your password has been changed successfully</p>
        <div className="success-box">
          You can now sign in with your new password.
        </div>
        <Link to="/login">
          <button className="btn">Sign in →</button>
        </Link>
      </div>
    </div>
  )

  return (
    <div className="page">
      <div className="card">
        <h1>Set new password</h1>
        <p className="subtitle">Enter your reset token and new password</p>

        {error && <div className="error-box">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Reset token</label>
            <input type="text" value={token}
              onChange={e => setToken(e.target.value)}
              placeholder="Paste your reset token" required
              style={{fontFamily:'monospace', fontSize:'0.85rem'}} />
          </div>
          <div className="form-group">
            <label>New password</label>
            <input type="password" value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Min 8 chars, upper, lower, number, symbol" required />
          </div>
          <div className="form-group">
            <label>Confirm new password</label>
            <input type="password" value={confirm}
              onChange={e => setConfirm(e.target.value)}
              placeholder="Repeat your new password" required />
          </div>
          <button className="btn" type="submit" disabled={loading}>
            {loading ? 'Updating…' : 'Update password'}
          </button>
        </form>

        <div className="link-row">
          <Link to="/login">Back to sign in</Link>
        </div>
      </div>
    </div>
  )
}
