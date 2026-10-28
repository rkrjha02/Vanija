import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  saveTokens,
} from './auth'
import type { ButtonResult, ChatReply, HistoryMessage } from './types'

export function resolveBaseUrl(envValue: string | undefined): string {
  if (!envValue) return '/api'
  return envValue.replace(/\/+$/, '')
}

const BASE_URL = resolveBaseUrl(import.meta.env.VITE_API_BASE_URL)
const REQUEST_TIMEOUT_MS = 180_000

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function authHeaders(): Record<string, string> {
  const token = getAccessToken()
  if (!token) return {}
  return { Authorization: `Bearer ${token}` }
}

async function rawRequest<T>(
  path: string,
  method: 'GET' | 'POST',
  body?: unknown,
): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
  try {
    const headers: Record<string, string> = { ...authHeaders() }
    if (body !== undefined) headers['Content-Type'] = 'application/json'

    const response = await fetch(BASE_URL + path, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    })
    if (!response.ok) {
      throw new ApiError(response.status, await response.text())
    }
    return (await response.json()) as T
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(0, 'The request took too long.')
    }
    throw error
  } finally {
    clearTimeout(timer)
  }
}

let refreshing: Promise<boolean> | null = null

async function doRefresh(): Promise<boolean> {
  const token = getRefreshToken()
  if (!token) return false
  try {
    const resp = await fetch(BASE_URL + '/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: token }),
    })
    if (!resp.ok) return false
    const data = (await resp.json()) as {
      access_token: string
      refresh_token: string
    }
    saveTokens(data.access_token, data.refresh_token)
    return true
  } catch {
    return false
  }
}

async function request<T>(
  path: string,
  method: 'GET' | 'POST',
  body?: unknown,
): Promise<T> {
  try {
    return await rawRequest<T>(path, method, body)
  } catch (error) {
    if (!(error instanceof ApiError && error.status === 401)) throw error
    if (!refreshing) refreshing = doRefresh()
    const ok = await refreshing
    refreshing = null
    if (!ok) {
      clearTokens()
      window.location.href = '/login'
      throw error
    }
    return rawRequest<T>(path, method, body)
  }
}

// --- Auth API ---

interface AuthResponse {
  access_token: string
  refresh_token: string
  customer_id: string
  name: string
}

export async function signup(
  name: string,
  email: string,
  password: string,
): Promise<AuthResponse> {
  return rawRequest<AuthResponse>('/auth/signup', 'POST', {
    name,
    email,
    password,
  })
}

export async function login(
  email: string,
  password: string,
): Promise<AuthResponse> {
  return rawRequest<AuthResponse>('/auth/login', 'POST', { email, password })
}

export async function logout(): Promise<void> {
  const token = getRefreshToken()
  if (token) {
    try {
      await rawRequest('/auth/logout', 'POST', { refresh_token: token })
    } catch {
      // best-effort
    }
  }
  clearTokens()
}

export async function adminLogin(
  username: string,
  password: string,
): Promise<{ access_token: string }> {
  return rawRequest<{ access_token: string }>('/admin/login', 'POST', {
    username,
    password,
  })
}

// --- Customer-facing API ---

export async function getHistory(): Promise<HistoryMessage[]> {
  const result = await request<{ messages: HistoryMessage[] }>('/history', 'GET')
  return result.messages
}

export function sendMessage(message: string): Promise<ChatReply> {
  return request<ChatReply>('/chat', 'POST', { message })
}

export function confirmOrder(
  pendingId: number,
  saveAddress: boolean,
): Promise<ButtonResult> {
  return request<ButtonResult>('/orders/confirm', 'POST', {
    pending_id: pendingId,
    save_address: saveAddress,
  })
}

export function confirmCancel(orderId: number): Promise<ButtonResult> {
  return request<ButtonResult>('/orders/cancel', 'POST', {
    order_id: orderId,
  })
}
