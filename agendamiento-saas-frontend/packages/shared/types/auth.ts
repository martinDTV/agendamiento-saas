import type { Tenant } from './tenant'

export type MembershipRole = 'owner' | 'admin' | 'doctor' | 'support' | 'staff'

export interface Membership {
  id: string
  tenant: Tenant
  role: MembershipRole
  is_active: boolean
  user_email: string
  user_uuid: string
  created_at: string
}

export interface AuthUser {
  id: number
  email: string
  first_name: string
  last_name: string
  memberships: Membership[]
  profile_picture_url?: string | null
}

export interface AuthTokens {
  access: string
  refresh: string
}
