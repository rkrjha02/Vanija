/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const BACKEND_URL = 'http://127.0.0.1:8000'
// Longer than the slowest chat turn (5 LLM rounds plus retries).
const PROXY_TIMEOUT_MS = 180_000

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: BACKEND_URL,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        timeout: PROXY_TIMEOUT_MS,
        proxyTimeout: PROXY_TIMEOUT_MS,
      },
    },
  },
  test: {
    environment: 'node',
  },
})
