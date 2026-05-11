/**
 * Blocks pages that should only be accessed by admin/owner roles.
 * Use as: definePageMeta({ middleware: ['tenant', 'auth', 'admin-only'] })
 */
export default defineNuxtRouteMiddleware(() => {
  if (import.meta.server) return

  const { isAdmin } = useRole()
  if (!isAdmin.value) {
    return navigateTo('/agenda')
  }
})
