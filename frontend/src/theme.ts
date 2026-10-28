import { useSyncExternalStore } from 'react'

export type Theme = 'light' | 'dark'

// The same key is read by the small script in index.html, so the saved theme applies before the first paint.
const THEME_KEY = 'vanija-theme'
const META_COLORS: Record<Theme, string> = { light: '#f8fafc', dark: '#0b1120' }

function savedTheme(): Theme | null {
  try {
    const value = localStorage.getItem(THEME_KEY)
    return value === 'light' || value === 'dark' ? value : null
  } catch {
    return null
  }
}

function darkQuery(): MediaQueryList | null {
  return typeof window !== 'undefined' && window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null
}

// One shared value, so every theme button on the screen shows the same state.
let current: Theme = savedTheme() ?? (darkQuery()?.matches ? 'dark' : 'light')
const listeners = new Set<() => void>()

function setCurrent(theme: Theme): void {
  current = theme
  listeners.forEach((listener) => listener())
}

// With no saved choice, follow the device when it switches between light and dark.
darkQuery()?.addEventListener('change', (event) => {
  if (!savedTheme()) setCurrent(event.matches ? 'dark' : 'light')
})

function subscribe(listener: () => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function toggleTheme(): void {
  const next: Theme = current === 'dark' ? 'light' : 'dark'
  document.documentElement.setAttribute('data-theme', next)
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', META_COLORS[next])
  try {
    localStorage.setItem(THEME_KEY, next)
  } catch { /* storage blocked: the choice lasts until reload */ }
  setCurrent(next)
}

export function useTheme(): Theme {
  return useSyncExternalStore(subscribe, () => current, () => 'light')
}
