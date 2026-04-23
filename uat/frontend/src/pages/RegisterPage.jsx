import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { register, getErrorMessage } from '../api'

export default function RegisterPage({ onLogin }) {
  const [email,    setEmail]    = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirm,  setConfirm]  = useState('')
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (password !== confirm) {
      setError('Passwords do not match')
      return
    }
    setLoading(true)
    try {
      const res = await register(email, password, username)
      onLogin(res.data.user, res.data.access_token)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <div className="card">
        <h1>Create account</h1>
        <p className="subtitle">Join the SynPro platform</p>

        {error && <div className="error-box">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email address</label>
            <input type="email" value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com" required />
          </div>
          <div className="form-group">
            <label>Username <span style={{color:'var(--muted)',fontWeight:400}}>(optional)</span></label>
            <input type="text" value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="yourname" />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Min 8 chars, upper, lower, number, symbol" required />
          </div>
          <div className="form-group">
            <label>Confirm password</label>
            <input type="password" value={confirm}
              onChange={e => setConfirm(e.target.value)}
              placeholder="Repeat your password" required />
          </div>
          <button className="btn" type="submit" disabled={loading}>
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <hr className="divider" />
        <div className="link-row">
          Already have an account? <Link to="/login">Sign in</Link>
        </div>
      </div>
    </div>
  )
}
