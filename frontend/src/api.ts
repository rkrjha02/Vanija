import type { ButtonResult, ChatReply, HistoryMessage } from './types'

const BASE_URL = '/api'
// Longer than the slowest chat turn (5 LLM rounds plus retries).
const REQUEST_TIMEOUT_MS = 180_000
const CUSTOMER_ID_KEY = 'electronics-agent-customer-id'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, method: 'GET' | 'POST', body?: unknown): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
  try {
    const response = await fetch(BASE_URL + path, {
      method,
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
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

function readStoredCustomerId(): string | null {
  try {
    return localStorage.getItem(CUSTOMER_ID_KEY)
  } catch {
    return null
  }
}

function storeCustomerId(customerId: string): void {
  try {
    localStorage.setItem(CUSTOMER_ID_KEY, customerId)
  } catch {
    // Storage blocked (private window): the chat still works, it just starts fresh on reload.
  }
}

export async function createCustomer(): Promise<string> {
  const result = await request<{ customer_id: string }>('/customers', 'POST')
  storeCustomerId(result.customer_id)
  return result.customer_id
}

export async function getHistory(customerId: string): Promise<HistoryMessage[]> {
  const result = await request<{ messages: HistoryMessage[] }>(
    `/history/${encodeURIComponent(customerId)}`,
    'GET',
  )
  return result.messages
}

export async function startSession(): Promise<{ customerId: string; history: HistoryMessage[] }> {
  const stored = readStoredCustomerId()
  if (stored) {
    try {
      return { customerId: stored, history: await getHistory(stored) }
    } catch (error) {
      if (!(error instanceof ApiError && error.status === 404)) throw error
    }
  }
  return { customerId: await createCustomer(), history: [] }
}

export function sendMessage(customerId: string, message: string): Promise<ChatReply> {
  return request<ChatReply>('/chat', 'POST', { customer_id: customerId, message })
}

export function confirmOrder(
  customerId: string,
  pendingId: number,
  saveAddress: boolean,
): Promise<ButtonResult> {
  return request<ButtonResult>('/orders/confirm', 'POST', {
    customer_id: customerId,
    pending_id: pendingId,
    save_address: saveAddress,
  })
}

export function confirmCancel(customerId: string, orderId: number): Promise<ButtonResult> {
  return request<ButtonResult>('/orders/cancel', 'POST', {
    customer_id: customerId,
    order_id: orderId,
  })
}
