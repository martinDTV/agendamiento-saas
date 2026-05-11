import { defineStore } from 'pinia'
import axios from 'axios'
import type { AuthUser, AuthTokens } from '@agendamiento/shared'

const ACCESS_KEY = 'auth:access'
const REFRESH_KEY = 'auth:refresh'

// Raw instance for auth-only endpoints — no interceptors to avoid recursion
const authHttp = axios.create({ headers: { 'Content-Type': 'application/json' } })

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as AuthUser | null,
    access: null as string | null,
    refresh: null as string | null,
    mustChangePassword: false
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

    setTokens(tokens: AuthTokens) {
      this.access = tokens.access
      this.refresh = tokens.refresh
      if (import.meta.client) {
        localStorage.setItem(ACCESS_KEY, tokens.access)
        localStorage.setItem(REFRESH_KEY, tokens.refresh)
      }
    },

    async login(email: string, password: string) {
      const config = useRuntimeConfig()
      const res = await authHttp.post<AuthTokens & { must_change_password?: boolean }>(
        `${config.public.apiBase}/user/auth/login/`,
        { email, password }
      )
      this.setTokens(res.data)
      this.mustChangePassword = !!res.data.must_change_password
      await this.fetchMe()
    },

    async fetchMe() {
      const { $api } = useNuxtApp()
      try {
        const res = await $api.get<AuthUser & { must_change_password?: boolean }>('/accounts/me/')
        this.user = res.data
        // Sobrescribir con el valor del backend (autoritativo, sobrevive reloads)
        this.mustChangePassword = !!res.data.must_change_password
      }
      catch {
        this.logout()
      }
    },

    async refreshAccessToken() {
      const config = useRuntimeConfig()
      try {
        const res = await authHttp.post<AuthTokens>(
          `${config.public.apiBase}/user/auth/refresh-token/`,
          { refresh: this.refresh }
        )
        this.setTokens(res.data)
        return true
      }
      catch {
        this.logout()
        return false
      }
    },

    roleForTenant(slug: string) {
      return this.user?.memberships.find(m => m.tenant.slug === slug)?.role ?? null
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
