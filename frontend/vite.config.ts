import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // Proxy /api requests to the backend during development.
    // In production the frontend and backend share an origin, so relative paths work directly.
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
