import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Dev-only proxy: forward /api requests to the FastAPI backend.
    // This lets the frontend use relative paths (/api/v1/...) in dev
    // without needing CORS — same behaviour as production (same-origin).
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
