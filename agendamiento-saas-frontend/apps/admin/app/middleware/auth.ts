export default defineNuxtRouteMiddleware((to) => {
  // Tokens live in localStorage — not available during SSR. Skip server-side.
  if (import.meta.server) return
  if (to.path === '/login') return
  const auth = useAuthStore()
  if (!auth.isAuthenticated) return navigateTo('/login')
  // Si la contraseña es temporal, no se puede navegar a otra cosa.
  if (auth.mustChangePassword && to.path !== '/cambiar-contrasena') {
    return navigateTo('/cambiar-contrasena')
  }
})
