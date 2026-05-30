export default defineNuxtConfig({
  modules: ['@nuxt/eslint', '@nuxt/ui'],

  devtools: { enabled: true },

  css: ['~/assets/css/main.css'],

  colorMode: {
    preference: 'light',
    fallback: 'light'
  },

  ui: {
    theme: {
      colors: ['primary', 'secondary', 'success', 'info', 'warning', 'error', 'navy', 'violet']
    }
  },

  // Served via SSR (Nitro node-server) behind Caddy. Prerendering all routes
  // spikes memory during build and OOMs on the small droplet, so we skip it;
  // the pages are still fully server-rendered and cacheable.
  nitro: {
    prerender: { crawlLinks: false, routes: [] }
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/rest/v1'
    }
  },

  compatibilityDate: '2025-01-15',

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  }
})
