import { defineStore } from 'pinia'
import axios from 'axios'

const ACCESS_KEY = 'platform:access'
const REFRESH_KEY = 'platform:refresh'

const authHttp = axios.create({ headers: { 'Content-Type': 'application/json' } })

interface PlatformUser {
  id: number
  email: string
  full_name: string
  is_superuser: boolean
}

export const usePlatformAuthStore = defineStore('platform-auth', {
  state: () => ({
    user: null as PlatformUser | null,
    access: null as string | null,
    refresh: null as string | null
  }),

  getters: {
    isAuthenticated: state => !!state.access && !!state.user
  },

  actions: {
    hydrate() {
      if (import.meta.client) {
        this.access = localStorage.getItem(ACCESS_KEY)
        this.refresh = localStorage.getItem(REFRESH_KEY)
      }
    },

    setTokens(access: string, refresh: string) {
      this.access = access
      this.refresh = refresh
      if (import.meta.client) {
        localStorage.setItem(ACCESS_KEY, access)
        localStorage.setItem(REFRESH_KEY, refresh)
      }
    },

    async login(email: string, password: string) {
      const config = useRuntimeConfig()
      const res = await authHttp.post<{ access: string; refresh: string; user: PlatformUser }>(
        `${config.public.apiBase}/platform/auth/login/`,
        { email, password }
      )
      this.setTokens(res.data.access, res.data.refresh)
      this.user = res.data.user
    },

    async fetchMe() {
      const { $api } = useNuxtApp()
      try {
        const res = await $api.get<PlatformUser>('/platform/auth/me/')
        this.user = res.data
      } catch {
        this.logout()
      }
    },

    logout() {
      this.user = null
      this.access = null
      this.refresh = null
      if (import.meta.client) {
        localStorage.removeItem(ACCESS_KEY)
        localStorage.removeItem(REFRESH_KEY)
      }
    }
  }
})
