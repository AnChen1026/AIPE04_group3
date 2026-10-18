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
    // 前端呼叫後端一律走 /backend，轉給 FastAPI 時拿掉這段前綴。
    // 瀏覽器視為同源，Session Cookie 會自動帶上；網址列上的頁面路徑都交給 Vue Router。
    proxy: {
      '/backend': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        ws: true,
        rewrite: (path) => path.replace(/^\/backend/, ''),
      },
    },
  },
})
