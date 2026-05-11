export default defineNuxtRouteMiddleware((to) => {
  if (import.meta.server) return
  if (to.path === '/login') return
  const auth = usePlatformAuthStore()
  if (!auth.isAuthenticated) return navigateTo('/login')
})
