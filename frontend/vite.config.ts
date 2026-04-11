import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()], // This adds react support -- adds the Babel transform for JSX and enables hot module replacement
  server: {
    // Frontend runs on localhost:5173 (Vite's default port) and backend runs on localhost:8000
    // Browsers block requests across different ports by default (Cross-origin resource sharing CORS)
    // So it just calls /api/hymn/assemble and Vite silently forwards it to the backend
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
