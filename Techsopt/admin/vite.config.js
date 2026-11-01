import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // Load project-level Vercel environment variables during the frontend build.
  // Only the Supabase project URL and publishable/anon key are exposed to browsers.
  const env = loadEnv(mode, '..', '')

  return {
    base: '/admin/',
    plugins: [react()],
    define: {
      'import.meta.env.VITE_SUPABASE_URL': JSON.stringify(env.SUPABASE_URL || ''),
      'import.meta.env.VITE_SUPABASE_ANON_KEY': JSON.stringify(
        env.SUPABASE_ANON_KEY || env.SUPABASE_PUBLISHABLE_KEY || ''
      ),
    },
    build: {
      // The Vercel admin service publishes dist/; nesting the bundle under
      // admin/ makes /admin/* resolve correctly when Vercel preserves the path.
      outDir: 'dist/admin',
      emptyOutDir: true,
    },
    server: {
      port: 5173,
      proxy: {
        '/api': 'http://127.0.0.1:8001',
      },
    },
  }
})
