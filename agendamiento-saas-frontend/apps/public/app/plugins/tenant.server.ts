/**
 * Server-side tenant resolution plugin.
 *
 * Runs only on the server during SSR. Parses the request Host header to extract
 * the tenant slug, fetches the tenant from the API, and hydrates the Pinia store
 * so the client receives it without an extra round-trip.
 *
 * Host patterns resolved:
 *   {slug}.miapp.com         → public site
 *   admin.{slug}.miapp.com   → (admin app handles this)
 *   {custom-domain}          → passed as slug lookup to the API
 */

import { useTenantStore } from '~/stores/tenant'
import type { Tenant } from '@agendamiento/shared'

export default defineNuxtPlugin(async (nuxtApp) => {
  if (import.meta.client) return

  const event = useRequestEvent()
  if (!event) return

  const host = event.node.req.headers.host ?? ''
  const slug = extractSlug(host, useRuntimeConfig().public.platformDomain)

  if (!slug) return

  try {
    const tenant = await $fetch<Tenant>(
      `${useRuntimeConfig().public.apiBase}/tenants/resolve/${slug}/`,
      { method: 'GET' }
    )
    const store = useTenantStore(nuxtApp.$pinia as Parameters<typeof useTenantStore>[0])
    store.setTenant(tenant)
  }
  catch (err) {
    // Let the page handle a missing tenant (error.vue or middleware)
    console.warn(`[tenant] Could not resolve tenant for host "${host}":`, err)
  }
})

function extractSlug(host: string, platformDomain: string): string | null {
  const bare = host.split(':')[0].toLowerCase()

  if (!bare.endsWith(platformDomain)) {
    // Custom domain — pass the full domain as the lookup key
    return bare || null
  }

  const prefix = bare.slice(0, bare.length - platformDomain.length).replace(/\.$/, '')
  if (!prefix) return null

  const parts = prefix.split('.')
  if (parts[0] === 'admin' && parts.length >= 2) return parts[1]
  return parts[0] ?? null
}
