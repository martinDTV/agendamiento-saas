export default defineNuxtConfig({
  modules: ['@nuxt/ui', '@nuxt/eslint', '@pinia/nuxt', '@vueuse/nuxt'],

  devtools: { enabled: true },

  components: [{ path: '~/components', pathPrefix: false }],

  css: ['~/assets/css/main.css'],

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/rest/v1'
    }
  },

  colorMode: {
    preference: 'light'
  },

  compatibilityDate: '2025-01-15',

  ssr: true,

  vite: {
    optimizeDeps: { include: ['axios'] }
  },

  eslint: {
    config: {
      stylistic: { commaDangle: 'never', braceStyle: '1tbs' }
    }
  }
})
