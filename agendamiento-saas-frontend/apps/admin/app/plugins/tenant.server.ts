import { useTenantStore } from '~/stores/tenant'
import type { Tenant } from '@agendamiento/shared'

export default defineNuxtPlugin(async (nuxtApp) => {
  if (import.meta.client) return

  const event = useRequestEvent()
  if (!event) return

  const config = useRuntimeConfig()
  const host = event.node.req.headers.host ?? ''

  // 1. Try to extract from host: admin.{slug}.miapp.com
  // 2. Fallback to NUXT_TENANT_SLUG env var (useful for localhost dev)
  const slug = extractAdminSlug(host, config.public.platformDomain) || config.tenantSlug

  if (!slug) return

  try {
    const tenant = await $fetch<Tenant>(
      `${config.public.apiBase}/tenants/resolve/${slug}/`,
      { method: 'GET' }
    )
    const store = useTenantStore(nuxtApp.$pinia as Parameters<typeof useTenantStore>[0])
    store.setTenant(tenant)
  }
  catch (err) {
    console.warn(`[tenant:admin] Could not resolve tenant for host "${host}" (slug: "${slug}"):`, err)
  }
})

function extractAdminSlug(host: string, platformDomain: string): string | null {
  const bare = host.split(':')[0].toLowerCase()
  if (!bare.endsWith(platformDomain)) return null

  const prefix = bare.slice(0, bare.length - platformDomain.length).replace(/\.$/, '')
  if (!prefix) return null
  const parts = prefix.split('.')

  // admin.{slug}.miapp.com → parts = ['admin', '{slug}']
  if (parts[0] === 'admin' && parts.length >= 2) return parts[1] ?? null

  // Demo: {slug}.demo-agendamiento.nexosoftdev.com — the admin is served under
  // /panel on the same clinic subdomain, so the slug is the first label.
  return parts[0] ?? null
}
