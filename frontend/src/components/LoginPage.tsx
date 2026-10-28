import { useState, type FormEvent } from 'react'
import { login, signup, ApiError } from '../api'
import { saveName, saveTokens } from '../auth'
import { STORE_NAME } from '../brand'
import { SparkIcon } from './Icons'

interface Props {
  onLogin: () => void
}

export function LoginPage({ onLogin }: Props) {
  const [tab, setTab] = useState<'login' | 'signup'>('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      if (tab === 'signup') {
        const res = await signup(name.trim(), email.trim(), password)
        saveTokens(res.access_token, res.refresh_token)
        saveName(res.name)
      } else {
        const res = await login(email.trim(), password)
        saveTokens(res.access_token, res.refresh_token)
        saveName(res.name)
      }
      onLogin()
    } catch (err) {
      if (err instanceof ApiError) {
        try {
          const parsed = JSON.parse(err.message)
          setError(typeof parsed.detail === 'string' ? parsed.detail : 'Something went wrong.')
        } catch {
          setError(err.message || 'Something went wrong.')
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
            <SparkIcon size={26} />
          </div>
          <h1 className="login-title">{STORE_NAME}</h1>
        </div>

        <div className="login-tabs">
          <button
            type="button"
            className={`login-tab ${tab === 'login' ? 'active' : ''}`}
            onClick={() => { setTab('login'); setError('') }}
          >
            Log in
          </button>
          <button
            type="button"
            className={`login-tab ${tab === 'signup' ? 'active' : ''}`}
            onClick={() => { setTab('signup'); setError('') }}
          >
            Sign up
          </button>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          {tab === 'signup' && (
            <label className="login-field">
              <span className="login-label">Name</span>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                autoComplete="name"
                disabled={busy}
              />
            </label>
          )}
          <label className="login-field">
            <span className="login-label">Email</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
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
              minLength={8}
              autoComplete={tab === 'signup' ? 'new-password' : 'current-password'}
              disabled={busy}
            />
          </label>
          {error && <div className="login-error">{error}</div>}
          <button type="submit" className="btn btn-accent btn-block" disabled={busy}>
            {busy ? (tab === 'signup' ? 'Creating account…' : 'Logging in…') : (tab === 'signup' ? 'Create account' : 'Log in')}
          </button>
        </form>
      </div>
    </div>
  )
}
