import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: true,
    allowedHosts: [
      'expo.artinsmartagent.com',
      'localhost',
      '127.0.0.1'
    ],
    // Proxy removed - use VITE_API_URL environment variable instead
  },
})
