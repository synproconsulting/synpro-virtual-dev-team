import React, { useState, useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import ResetRequestPage from './pages/ResetRequestPage'
import ResetCompletePage from './pages/ResetCompletePage'

export default function App() {
  const [user, setUser]   = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token'))

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token)
    } else {
      localStorage.removeItem('token')
    }
  }, [token])

  const login = (userData, accessToken) => {
    setUser(userData)
    setToken(accessToken)
  }

  const logout = () => {
    setUser(null)
    setToken(null)
  }

  return (
    <Routes>
      <Route path="/"
        element={token ? <Navigate to="/dashboard" /> : <Navigate to="/login" />}
      />
      <Route path="/login"
        element={token ? <Navigate to="/dashboard" /> : <LoginPage onLogin={login} />}
      />
      <Route path="/register"
        element={token ? <Navigate to="/dashboard" /> : <RegisterPage onLogin={login} />}
      />
      <Route path="/dashboard"
        element={token ? <DashboardPage user={user} token={token} onLogout={logout} />
                       : <Navigate to="/login" />}
      />
      <Route path="/reset-password"       element={<ResetRequestPage />} />
      <Route path="/reset-password/complete" element={<ResetCompletePage />} />
    </Routes>
  )
}
