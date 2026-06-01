/**
 * Pull a human-readable message out of a DRF/axios error.
 *
 * Handles the common shapes:
 *   { detail: "..." }
 *   { start_time: ["Este horario ya no está disponible."] }
 *   { non_field_errors: ["..."] }
 *   plain string
 * Falls back to `fallback` when nothing usable is found.
 */
export function extractApiError(error: unknown, fallback = 'Ocurrió un error. Intenta de nuevo.'): string {
  const data = (error as { response?: { data?: unknown } })?.response?.data

  if (typeof data === 'string' && data.trim()) return data
  if (data && typeof data === 'object') {
    const obj = data as Record<string, unknown>
    if (typeof obj.detail === 'string' && obj.detail.trim()) return obj.detail

    // First field error (e.g. start_time: ["..."]).
    for (const value of Object.values(obj)) {
      if (typeof value === 'string' && value.trim()) return value
      if (Array.isArray(value) && typeof value[0] === 'string' && value[0].trim()) {
        return value[0]
      }
    }
  }
  return fallback
}
