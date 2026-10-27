import { resolveBaseUrl } from './api'

const BASE_URL = resolveBaseUrl(import.meta.env.VITE_API_BASE_URL)

export interface AdminProduct {
  id: string
  name: string
  category: string
  brand: string | null
  price: number
  stock: number
  description: string | null
  short_description: string | null
  specs: Record<string, string | number | boolean> | null
  tags: string[] | null
  is_active: boolean
  has_embedding: boolean
}

export interface ProductListResponse {
  total: number
  page: number
  page_size: number
  products: AdminProduct[]
}

export interface UploadResult {
  added: number
  skipped: number
  skipped_names: string[]
  embedded: number
  errors: { row: number; reason: string }[]
}

async function adminRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const resp = await fetch(BASE_URL + path, options)
  if (!resp.ok) {
    const body = await resp.text()
    let detail = body
    try {
      const parsed = JSON.parse(body)
      detail = typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail)
    } catch { /* use raw text */ }
    throw new Error(detail)
  }
  return resp.json() as Promise<T>
}

function json(body: unknown): RequestInit {
  return {
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}

export function fetchCategories(): Promise<string[]> {
  return adminRequest('/admin/categories')
}

export function fetchProducts(params: Record<string, string>): Promise<ProductListResponse> {
  const qs = new URLSearchParams(params).toString()
  return adminRequest(`/admin/products?${qs}`)
}

export function fetchProduct(id: string): Promise<AdminProduct> {
  return adminRequest(`/admin/products/${encodeURIComponent(id)}`)
}

export function createProduct(data: Record<string, unknown>): Promise<AdminProduct> {
  return adminRequest('/admin/products', { method: 'POST', ...json(data) })
}

export function updateProduct(id: string, data: Record<string, unknown>): Promise<AdminProduct> {
  return adminRequest(`/admin/products/${encodeURIComponent(id)}`, { method: 'PUT', ...json(data) })
}

export function deleteProduct(id: string): Promise<{ status: string }> {
  return adminRequest(`/admin/products/${encodeURIComponent(id)}`, { method: 'DELETE' })
}

export function reactivateProduct(id: string): Promise<AdminProduct> {
  return adminRequest(`/admin/products/${encodeURIComponent(id)}/reactivate`, { method: 'POST' })
}

export async function uploadCsv(file: File): Promise<UploadResult> {
  const form = new FormData()
  form.append('file', file)
  return adminRequest('/admin/products/upload', { method: 'POST', body: form })
}
