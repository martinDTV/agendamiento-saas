import { useTenantStore } from '~/stores/tenant'

/**
 * Route middleware: redirects to an error page if no tenant was resolved.
 * Runs on every navigation after the server plugin has hydrated the store.
 */
export default defineNuxtRouteMiddleware(() => {
  const store = useTenantStore()
  if (!store.isLoaded) {
    throw createError({ statusCode: 404, message: 'Tenant no encontrado' })
  }
})
