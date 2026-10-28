import { useState, type FormEvent } from 'react'
import { adminLogin, ApiError } from '../api'
import { saveAdminToken } from '../auth'
import { STORE_NAME } from '../brand'
import { SettingsIcon } from './Icons'

interface Props {
  onLogin: () => void
}

export function AdminLoginPage({ onLogin }: Props) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      const res = await adminLogin(username.trim(), password)
      saveAdminToken(res.access_token)
      onLogin()
    } catch (err) {
      if (err instanceof ApiError) {
        try {
          const parsed = JSON.parse(err.message)
          setError(typeof parsed.detail === 'string' ? parsed.detail : 'Invalid credentials.')
        } catch {
          setError(err.message || 'Invalid credentials.')
        }
      } else {
        setError('Could not reach the server. Please try again.')
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <div className="store-mark lg" aria-hidden="true">
            <SettingsIcon size={26} />
          </div>
          <h1 className="login-title">{STORE_NAME}</h1>
          <p className="login-subtitle">Admin Panel</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label className="login-field">
            <span className="login-label">Username</span>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
              autoFocus
              disabled={busy}
            />
          </label>
          <label className="login-field">
            <span className="login-label">Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              disabled={busy}
            />
          </label>
          {error && <div className="login-error">{error}</div>}
          <button type="submit" className="btn btn-accent btn-block" disabled={busy}>
            {busy ? 'Logging in…' : 'Log in'}
          </button>
        </form>
      </div>
    </div>
  )
}
