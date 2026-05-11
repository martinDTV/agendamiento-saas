import type { SiteContent } from './content'

export type TenantType = 'solo' | 'clinic'

export interface TenantSettings {
  branding?: {
    logoUrl?: string
    primaryColor?: string
    fontFamily?: string
  }
  timezone?: string
  locale?: string
  features?: Record<string, boolean>
  content?: Partial<SiteContent>
}

export interface PlanFlags {
  white_label?: boolean
  cms_editor?: boolean
  ai_booking_suggestions?: boolean
  chat_human_support?: boolean
  chat_ai_support?: boolean
}

export interface Tenant {
  id: string
  slug: string
  name: string
  type: TenantType
  plan: string
  plan_flags?: PlanFlags
  settings: TenantSettings
}
