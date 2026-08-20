import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: 'https://github.com/ludovicfmp-bit/OMet_V2/',  // Remplacez par le nom exact de votre dépôt
})