import { defineConfig } from 'vite'

export default defineConfig({
  root: 'src',
  server: {
    port: 8000,
    host: true,
    open: '/enhancedIndex.html' // Open enhanced version by default
  },
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: 'src/index.html',
        enhanced: 'src/enhancedIndex.html'
      }
    }
  },
  publicDir: '../public'
})