import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

export const register = (email, password, username) =>
  api.post('/auth/register', { email, password, username })

export const login = (email, password) =>
  api.post('/auth/login', { email, password })

export const requestPasswordReset = (email) =>
  api.post('/auth/password-reset/request', { email })

export const completePasswordReset = (token, new_password) =>
  api.post('/auth/password-reset/complete', { token, new_password })

export const getMe = (token) =>
  api.get('/auth/me', { headers: { Authorization: `Bearer ${token}` } })

export const getErrorMessage = (error) => {
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail
    if (typeof detail === 'string') return detail
    if (detail.message) {
      return detail.errors
        ? `${detail.message}: ${detail.errors.join(', ')}`
        : detail.message
    }
  }
  return 'Something went wrong. Please try again.'
}
