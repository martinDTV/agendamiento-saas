import { DEFAULT_CONTENT, type SiteContent } from '@agendamiento/shared'

type DeepPartial<T> = T extends Array<infer U>
  ? Array<DeepPartial<U>>
  : T extends object
    ? { [K in keyof T]?: DeepPartial<T[K]> }
    : T

function isPlainObject(v: unknown): v is Record<string, unknown> {
  return v !== null && typeof v === 'object' && !Array.isArray(v)
}

function mergeDeep<T>(base: T, override: DeepPartial<T> | undefined): T {
  if (override === undefined || override === null) return base
  if (Array.isArray(base)) {
    return (Array.isArray(override) ? override : base) as T
  }
  if (isPlainObject(base)) {
    const out: Record<string, unknown> = { ...(base as Record<string, unknown>) }
    if (isPlainObject(override)) {
      for (const k of Object.keys(override)) {
        const b = (base as Record<string, unknown>)[k]
        const o = (override as Record<string, unknown>)[k]
        out[k] = mergeDeep(b as never, o as never)
      }
    }
    return out as T
  }
  return (override as T) ?? base
}

/**
 * Returns a fully-resolved SiteContent: defaults deep-merged with whatever
 * the tenant has saved in settings.content. Reactive — re-computes if the
 * tenant store updates.
 */
export function useContent() {
  const tenant = useTenantStore()
  const content = computed<SiteContent>(() =>
    mergeDeep(DEFAULT_CONTENT, tenant.tenant?.settings?.content as DeepPartial<SiteContent> | undefined)
  )
  return { content }
}
