import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000, // 前端运行端口
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000', // 这里必须指向你的 Flask 后端
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})