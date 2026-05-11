export default defineNuxtConfig({
  modules: ['@nuxt/ui', '@nuxt/eslint', '@pinia/nuxt', '@vueuse/nuxt'],

  devtools: { enabled: true },

  components: [{ path: '~/components', pathPrefix: false }],

  css: ['~/assets/css/main.css'],

  runtimeConfig: {
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
