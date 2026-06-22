import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// Vite配置 - 企业知识库问答系统前端
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  // 开发服务器配置
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
  // 生产构建输出到 ../server/static 目录（Flask 直接托管）
  build: {
    outDir: path.resolve(__dirname, '../server/static'),
    emptyOutDir: true,
  },
})
