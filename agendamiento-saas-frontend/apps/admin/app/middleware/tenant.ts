import { useTenantStore } from '~/stores/tenant'

export default defineNuxtRouteMiddleware(() => {
  const store = useTenantStore()
  if (!store.isLoaded) {
    throw createError({ statusCode: 404, message: 'Tenant de administración no encontrado' })
  }
})
