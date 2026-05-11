import axios from 'axios'
import type { AxiosInstance } from 'axios'
import { useTenantStore } from '~/stores/tenant'

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
    const tenant = useTenantStore()
    if (tenant.slug) cfg.headers['X-Tenant-Slug'] = tenant.slug
    return cfg
  })

  return { provide: { api } }
})
