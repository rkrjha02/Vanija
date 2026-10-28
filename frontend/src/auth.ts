const ACCESS_KEY = 'access_token'
const REFRESH_KEY = 'refresh_token'
const ADMIN_KEY = 'admin_access_token'
const NAME_KEY = 'user_name'

export function saveTokens(accessToken: string, refreshToken: string): void {
  try {
    localStorage.setItem(ACCESS_KEY, accessToken)
    localStorage.setItem(REFRESH_KEY, refreshToken)
  } catch { /* storage blocked */ }
}

export function getAccessToken(): string | null {
  try { return localStorage.getItem(ACCESS_KEY) } catch { return null }
}

export function getRefreshToken(): string | null {
  try { return localStorage.getItem(REFRESH_KEY) } catch { return null }
}

export function clearTokens(): void {
  try {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
    localStorage.removeItem(NAME_KEY)
  } catch { /* storage blocked */ }
}

export function isLoggedIn(): boolean {
  return getAccessToken() !== null
}

export function saveName(name: string): void {
  try { localStorage.setItem(NAME_KEY, name) } catch { /* */ }
}

export function getName(): string | null {
  try { return localStorage.getItem(NAME_KEY) } catch { return null }
}

export function saveAdminToken(token: string): void {
  try { localStorage.setItem(ADMIN_KEY, token) } catch { /* */ }
}

export function getAdminToken(): string | null {
  try { return localStorage.getItem(ADMIN_KEY) } catch { return null }
}

export function clearAdminToken(): void {
  try { localStorage.removeItem(ADMIN_KEY) } catch { /* */ }
}

export function isAdminLoggedIn(): boolean {
  return getAdminToken() !== null
}
