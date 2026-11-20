import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: './',  // 相对路径，兼容 GitHub Pages 子路径部署
  server: {
    port: 5174,
    proxy: {
      '/api': 'http://127.0.0.1:8790',
    },
  },
})
