import { defineStore } from 'pinia'
import type { Tenant } from '@agendamiento/shared'

export const useTenantStore = defineStore('tenant', {
  state: (): { tenant: Tenant | null } => ({
    tenant: null
  }),

  getters: {
    isLoaded: (state) => state.tenant !== null,
    slug: (state) => state.tenant?.slug ?? null,
    primaryColor: (state) => state.tenant?.settings?.branding?.primaryColor ?? '#2563eb'
  },

  actions: {
    setTenant(tenant: Tenant) {
      this.tenant = tenant
    },
    clear() {
      this.tenant = null
    }
  }
})
