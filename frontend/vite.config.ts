import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  // Plotly is intentionally bundled for offline interactive analytics.
  build: { chunkSizeWarningLimit: 6000 },
})
