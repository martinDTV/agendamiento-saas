import axios from 'axios'
import type { AxiosInstance } from 'axios'

declare module '#app' {
  interface NuxtApp {
    $api: AxiosInstance
  }
}

export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig()
  const api = axios.create({
    baseURL: config.public.apiBase,
    headers: { 'Content-Type': 'application/json' }
  })

  api.interceptors.request.use((cfg) => {
    const auth = useAuthStore()
    const tenant = useTenantStore()
    if (auth.access) cfg.headers.Authorization = `Bearer ${auth.access}`
    if (tenant.slug) cfg.headers['X-Tenant-Slug'] = tenant.slug
    // FormData uploads: borra el Content-Type default para que axios añada
    // 'multipart/form-data; boundary=...' automáticamente.
    if (cfg.data instanceof FormData) {
      delete cfg.headers['Content-Type']
    }
    return cfg
  })

  api.interceptors.response.use(
    res => res,
    async (error) => {
      const auth = useAuthStore()
      if (error.response?.status === 401 && auth.refresh && !error.config._retry) {
        error.config._retry = true
        const ok = await auth.refreshAccessToken()
        if (ok) {
          error.config.headers.Authorization = `Bearer ${auth.access}`
          return api(error.config)
        }
      }
      return Promise.reject(error)
    }
  )

  return { provide: { api } }
})
