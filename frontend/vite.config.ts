import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { SvelteKitPWA } from '@vite-pwa/sveltekit';
import { defineConfig } from 'vite';
import devtoolsJson from 'vite-plugin-devtools-json';

export default defineConfig({
  plugins: [
    devtoolsJson(),
    tailwindcss(),
    sveltekit(),
    // https://vite-pwa-org.netlify.app/frameworks/sveltekit.html
    SvelteKitPWA({
      srcDir: './src',
      strategies: 'injectManifest',
      filename: 'service-worker.ts',
      scope: '/',
      base: '/',
      pwaAssets: {
        config: true
      },
      manifest: {
        short_name: 'Kaloscope',
        name: 'Kaloscope',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        theme_color: '#ffffff',
        background_color: '#ffffff'
      },
      injectManifest: {
        globPatterns: ['client/**/*.{js,css,ico,png,svg,webp,woff,woff2}']
      },
      devOptions: {
        enabled: true,
        type: 'module',
        navigateFallback: '/'
      },
      kit: {
        includeVersionFile: true
      }
    })
  ],
  server: {
    strictPort: true,
    host: '0.0.0.0',
    proxy: {
      '/_api': 'http://127.0.0.1:8000'
    }
  }
});
