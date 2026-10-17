import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // 後端 CORS 已允許 localhost:3000
    port: 3000,
    // /api 轉給 FastAPI，瀏覽器視為同源，Session Cookie 才會自動帶上
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      // 「與老師聯繫」會整頁前往後端：未登入先到登入頁，學生登入後打開聊天室
      '/courses': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/login': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/student': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/logout': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
