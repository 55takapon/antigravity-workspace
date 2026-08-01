import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: '体重記録',
        short_name: '体重記録',
        description: '体重を記録して推移を確認する個人用アプリ',
        start_url: '/',
        display: 'standalone',
        background_color: '#0f0906',
        theme_color: '#0f0906',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          {
            src: '/icons/icon-maskable-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
      },
      // オフライン時は「オフラインです」と表示するのみ。書き込みのキューイングはスコープ外
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,ico}'],
      },
    }),
  ],
  resolve: {
    alias: {
      // @/ を src/ に解決する
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
