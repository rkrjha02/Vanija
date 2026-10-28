import { useState, type FormEvent } from 'react'
import { login, signup, ApiError } from '../api'
import { saveName, saveTokens } from '../auth'
import { STORE_NAME, STORE_TAGLINE } from '../brand'
import { BrandMark } from './BrandMark'
import { AlertIcon, CashIcon, EyeIcon, EyeOffIcon, SearchIcon, ShieldIcon } from './Icons'
import { ThemeToggle } from './ThemeToggle'
import './auth.css'

interface Props {
  onLogin: () => void
}

type Field = 'name' | 'email' | 'password'
type Errors = Partial<Record<Field | 'form', string>>

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

// The backend's fixed error texts (api/auth.py), mapped to the field they belong to and a friendlier sentence.
const SERVER_ERRORS: Record<string, { field: Field | 'form'; text: string }> = {
  'Name is required': { field: 'name', text: 'Please enter your name.' },
  'Invalid email format': { field: 'email', text: 'Please enter a valid email address.' },
  'Password must be at least 8 characters': { field: 'password', text: 'Password must be at least 8 characters.' },
  'Email already registered': { field: 'email', text: 'This email is already registered.' },
  'Invalid email or password': { field: 'form', text: 'Incorrect email or password. Please try again.' },
}

function serverErrors(err: unknown): Errors {
  if (!(err instanceof ApiError)) return { form: 'Could not reach the server. Please check your connection and try again.' }
  if (err.status === 0) return { form: 'That took too long. Please try again.' }
  try {
    const detail = JSON.parse(err.message).detail
    const known = typeof detail === 'string' ? SERVER_ERRORS[detail] : undefined
    if (known) return { [known.field]: known.text }
  } catch { /* not JSON: fall through to a generic message */ }
  if (err.status === 401) return { form: SERVER_ERRORS['Invalid email or password'].text }
  if (err.status >= 500) return { form: 'Something went wrong on our side. Please try again in a moment.' }
  return { form: 'Please check your details and try again.' }
}

const FEATURES = [
  { icon: SearchIcon, title: 'Just describe what you need', text: 'Ask in your own words and get options that fit your budget.' },
  { icon: ShieldIcon, title: 'Real prices, real stock', text: 'Every price and stock level comes straight from our store.' },
  { icon: CashIcon, title: 'Cash on Delivery', text: 'Review your order, confirm with one tap, pay when it arrives.' },
]

export function LoginPage({ onLogin }: Props) {
  const [tab, setTab] = useState<'login' | 'signup'>('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState<Errors>({})
  const [busy, setBusy] = useState(false)

  function switchTab(next: 'login' | 'signup') {
    setTab(next)
    setErrors({})
  }

  function validate(): Errors {
    const found: Errors = {}
    if (tab === 'signup' && !name.trim()) found.name = 'Please enter your name.'
    if (!email.trim()) found.email = 'Please enter your email address.'
    else if (!EMAIL_PATTERN.test(email.trim())) found.email = 'Please enter a valid email address.'
    if (!password) found.password = 'Please enter your password.'
    else if (password.length < 8) found.password = 'Password must be at least 8 characters.'
    return found
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (busy) return
    const found = validate()
    setErrors(found)
    if (Object.keys(found).length > 0) return

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
      setErrors(serverErrors(err))
    } finally {
      setBusy(false)
    }
  }

  function clearError(field: Field) {
    if (errors[field] || errors.form) setErrors((current) => ({ ...current, [field]: undefined, form: undefined }))
  }

  const isSignup = tab === 'signup'
  const emailTaken = errors.email === SERVER_ERRORS['Email already registered'].text

  return (
    <div className="auth">
      <div className="auth-theme">
        <ThemeToggle />
      </div>

      <section className="auth-brand">
        <div className="brand-lockup">
          <BrandMark size="lg" />
          <div>
            <div className="brand-name">{STORE_NAME}</div>
            <div className="brand-tagline">{STORE_TAGLINE}</div>
          </div>
        </div>

        <h1 className="auth-headline">
          Smarter Shopping <span>Made Simple</span>
        </h1>
        <p className="auth-lead">
          Chat with Vanija to discover phones, laptops and headphones, get recommendations that fit your needs, and
          place your order without leaving the conversation.
        </p>

        <ul className="auth-features">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <li key={title}>
              <span className="auth-feature-icon">
                <Icon size={18} />
              </span>
              <div>
                <div className="auth-feature-title">{title}</div>
                <div className="auth-feature-text">{text}</div>
              </div>
            </li>
          ))}
        </ul>

        <div className="auth-preview" aria-hidden="true">
          <div className="preview-row user">
            <div className="preview-bubble">I need headphones for long flights</div>
          </div>
          <div className="preview-row">
            <BrandMark size="sm" />
            <div className="preview-bubble ai">Happy to help! Do you prefer noise cancelling over-ear, or something lighter?</div>
          </div>
          <div className="preview-row">
            <BrandMark size="sm" />
            <div className="preview-bubble ai typing">
              <span />
              <span />
              <span />
            </div>
          </div>
        </div>
      </section>

      <main className="auth-panel">
        <div className="auth-card">
          <div className="auth-card-head">
            <h2>{isSignup ? 'Create your account' : 'Welcome back'}</h2>
            <p>{isSignup ? 'Start shopping with Vanija in under a minute.' : 'Log in to continue shopping with Vanija.'}</p>
          </div>

          <div className="auth-tabs" role="tablist" aria-label="Log in or sign up">
            <button
              type="button"
              role="tab"
              aria-selected={!isSignup}
              className={`auth-tab ${!isSignup ? 'active' : ''}`}
              onClick={() => switchTab('login')}
              disabled={busy}
            >
              Login
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={isSignup}
              className={`auth-tab ${isSignup ? 'active' : ''}`}
              onClick={() => switchTab('signup')}
              disabled={busy}
            >
              Sign Up
            </button>
            <span className={`auth-tab-indicator ${isSignup ? 'right' : ''}`} aria-hidden="true" />
          </div>

          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            {isSignup && (
              <div className="auth-field">
                <label htmlFor="auth-name">Full name</label>
                <input
                  id="auth-name"
                  type="text"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value)
                    clearError('name')
                  }}
                  placeholder="e.g. Priya Sharma"
                  autoComplete="name"
                  autoFocus
                  disabled={busy}
                  aria-invalid={errors.name ? true : undefined}
                  aria-describedby={errors.name ? 'auth-name-error' : undefined}
                />
                {errors.name && (
                  <p id="auth-name-error" className="field-error">
                    {errors.name}
                  </p>
                )}
              </div>
            )}

            <div className="auth-field">
              <label htmlFor="auth-email">Email address</label>
              <input
                id="auth-email"
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                  clearError('email')
                }}
                placeholder="you@example.com"
                autoComplete="email"
                autoFocus={!isSignup}
                disabled={busy}
                aria-invalid={errors.email ? true : undefined}
                aria-describedby={errors.email ? 'auth-email-error' : undefined}
              />
              {errors.email && (
                <p id="auth-email-error" className="field-error">
                  {errors.email}
                  {emailTaken && (
                    <>
                      {' '}
                      <button type="button" className="link-button" onClick={() => switchTab('login')}>
                        Log in instead
                      </button>
                    </>
                  )}
                </p>
              )}
            </div>

            <div className="auth-field">
              <label htmlFor="auth-password">Password</label>
              <div className="password-wrap">
                <input
                  id="auth-password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value)
                    clearError('password')
                  }}
                  placeholder={isSignup ? 'Create a password' : 'Enter your password'}
                  autoComplete={isSignup ? 'new-password' : 'current-password'}
                  disabled={busy}
                  aria-invalid={errors.password ? true : undefined}
                  aria-describedby={[isSignup ? 'auth-password-hint' : '', errors.password ? 'auth-password-error' : '']
                    .filter(Boolean)
                    .join(' ') || undefined}
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  aria-pressed={showPassword}
                  disabled={busy}
                >
                  {showPassword ? <EyeOffIcon size={18} /> : <EyeIcon size={18} />}
                </button>
              </div>
              {isSignup && !errors.password && (
                <p id="auth-password-hint" className="field-hint">
                  Minimum 8 characters
                </p>
              )}
              {errors.password && (
                <p id="auth-password-error" className="field-error">
                  {errors.password}
                </p>
              )}
            </div>

            {errors.form && (
              <div className="form-alert" role="alert">
                <AlertIcon size={16} />
                <span>{errors.form}</span>
              </div>
            )}

            <button type="submit" className="btn btn-accent btn-block btn-lg" disabled={busy}>
              {busy && <span className="spinner" />}
              {busy ? (isSignup ? 'Creating account…' : 'Logging in…') : isSignup ? 'Create Account' : 'Login'}
            </button>
          </form>

          <p className="auth-switch">
            {isSignup ? 'Already have an account?' : 'New to Vanija?'}{' '}
            <button type="button" className="link-button" onClick={() => switchTab(isSignup ? 'login' : 'signup')} disabled={busy}>
              {isSignup ? 'Log in' : 'Create an account'}
            </button>
          </p>
        </div>
      </main>
    </div>
  )
}
