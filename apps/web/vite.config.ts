import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
    plugins: [react()],
    build: {
        rolldownOptions: {
            output: {
                // Bibliotecas em chunks próprios: mudam pouco, então o navegador as guarda entre deploys
                // (um deploy só do app não obriga a baixar React/Supabase de novo). Páginas e dashboards
                // já são separados pelos import() de App.tsx e dashboards/registry.tsx.
                codeSplitting: {
                    groups: [
                        { name: 'vendor-react', test: /node_modules[\\/](react|react-dom|scheduler)[\\/]/ },
                        { name: 'vendor-router', test: /node_modules[\\/]react-router[\\/]/ },
                        { name: 'vendor-supabase', test: /node_modules[\\/](@supabase|iceberg-js|tslib)[\\/]/ },
                        { name: 'vendor-dnd', test: /node_modules[\\/]@dnd-kit[\\/]/ },
                    ],
                },
            },
        },
    },
})
