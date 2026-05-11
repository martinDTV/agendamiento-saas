import type { MembershipRole } from '@agendamiento/shared'

/**
 * Returns the role of the current user in the active tenant.
 * Falls back to 'staff' if no membership found.
 */
export function useRole() {
  const auth   = useAuthStore()
  const tenant = useTenantStore()

  const role = computed<MembershipRole>(() => {
    const slug = tenant.slug
    const m = auth.user?.memberships?.find((x: any) => x.tenant_slug === slug)
                ?? auth.user?.memberships?.[0]
    return (m?.role as MembershipRole) ?? 'staff'
  })

  const isOwner  = computed(() => role.value === 'owner')
  const isAdmin  = computed(() => role.value === 'admin' || role.value === 'owner')
  const isDoctor = computed(() => role.value === 'doctor')
  const isStaff  = computed(() => role.value === 'staff')

  return { role, isOwner, isAdmin, isDoctor, isStaff }
}
