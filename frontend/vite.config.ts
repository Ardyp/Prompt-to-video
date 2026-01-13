import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import http from 'http'
import https from 'https'

// Create HTTP agents that force IPv4
const httpAgent = new http.Agent({ family: 4 })
const httpsAgent = new https.Agent({ family: 4 })

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        agent: httpAgent,
      },
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
        agent: httpAgent,
      },
      '/static': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        agent: httpAgent,
      },
    },
  },
})
