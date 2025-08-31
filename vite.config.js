import { defineConfig } from 'vite'

export default defineConfig({
  root: 'src',
  server: {
    port: 8000,
    host: true
  },
  build: {
    outDir: '../dist',
    emptyOutDir: true
  },
  publicDir: '../public'
})