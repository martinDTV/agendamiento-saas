import { defineStore } from 'pinia'

export interface PlatformSettings {
  primary_color: string
  platform_name: string
  support_email: string
  logo_url: string
  updated_at?: string
}

const DEFAULTS: PlatformSettings = {
  primary_color: '#6366f1',
  platform_name: 'Plataforma',
  support_email: '',
  logo_url: '',
  updated_at: undefined,
}

export const usePlatformSettingsStore = defineStore('platform-settings', {
  state: (): { settings: PlatformSettings; loaded: boolean } => ({
    settings: { ...DEFAULTS },
    loaded: false,
  }),

  actions: {
    set(settings: Partial<PlatformSettings>) {
      this.settings = { ...DEFAULTS, ...this.settings, ...settings }
      this.loaded = true
    },
  },
})
