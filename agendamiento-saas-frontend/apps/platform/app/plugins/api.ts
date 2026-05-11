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
    const auth = usePlatformAuthStore()
    if (auth.access) cfg.headers.Authorization = `Bearer ${auth.access}`
    // FormData uploads: borra el Content-Type default para que axios añada
    // 'multipart/form-data; boundary=...' automáticamente.
    if (cfg.data instanceof FormData) {
      delete cfg.headers['Content-Type']
    }
    return cfg
  })

  api.interceptors.response.use(
    res => res,
    (error) => {
      const auth = usePlatformAuthStore()
      if (error.response?.status === 401) {
        auth.logout()
        navigateTo('/login')
      }
      return Promise.reject(error)
    }
  )

  return { provide: { api } }
})
