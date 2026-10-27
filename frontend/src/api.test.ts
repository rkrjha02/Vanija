import { describe, expect, it } from 'vitest'
import { resolveBaseUrl } from './api'

describe('resolveBaseUrl', () => {
  it('returns /api when the env variable is undefined', () => {
    expect(resolveBaseUrl(undefined)).toBe('/api')
  })

  it('returns /api when the env variable is an empty string', () => {
    expect(resolveBaseUrl('')).toBe('/api')
  })

  it('returns the env value when set', () => {
    expect(resolveBaseUrl('https://backend.example.com')).toBe('https://backend.example.com')
  })

  it('strips a trailing slash from the env value', () => {
    expect(resolveBaseUrl('https://backend.example.com/')).toBe('https://backend.example.com')
  })

  it('strips multiple trailing slashes', () => {
    expect(resolveBaseUrl('https://backend.example.com///')).toBe('https://backend.example.com')
  })
})
