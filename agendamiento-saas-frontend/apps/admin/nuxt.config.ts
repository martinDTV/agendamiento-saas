export default defineNuxtConfig({
  modules: ['@nuxt/ui', '@nuxt/eslint', '@pinia/nuxt', '@vueuse/nuxt'],

  devtools: { enabled: true },

  // Served under a subpath in the demo (clinica.demo-.../panel). Defaults to '/'
  // for normal subdomain deployments.
  app: {
    baseURL: process.env.NUXT_APP_BASE_URL || '/'
  },

  components: [{ path: '~/components', pathPrefix: false }],

  css: ['~/assets/css/main.css'],

  runtimeConfig: {
    // Server-only: fallback slug for local dev (set NUXT_TENANT_SLUG=clinica-a in .env)
    tenantSlug: process.env.NUXT_TENANT_SLUG || '',
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/rest/v1',
      platformDomain: process.env.NUXT_PUBLIC_PLATFORM_DOMAIN || 'miapp.com'
    }
  },

  colorMode: {
    preference: 'light'
  },

  compatibilityDate: '2025-01-15',

  ssr: true,

  vite: {
    optimizeDeps: {
      include: ['axios']
    },
    server: {
      allowedHosts: ['.miapp.com']
    }
  },

  eslint: {
    config: {
      stylistic: { commaDangle: 'never', braceStyle: '1tbs' }
    }
  }
})
