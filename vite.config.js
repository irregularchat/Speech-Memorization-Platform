import { defineConfig } from 'vite'

export default defineConfig({
  root: 'src',
  server: {
    port: 8000,
    host: true,
    open: 'enhancedIndex.html' // Open enhanced version by default
  },
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: './index.html',
        enhanced: './enhancedIndex.html'
      }
    }
  },
  publicDir: '../public'
})