/**
 * Loads the platform's public settings (name, primary color, logo) on the
 * client right after Nuxt mounts so the login screen and authenticated pages
 * already show the super-admin-chosen branding.
 *
 * Endpoint is unauthenticated (only exposes safe-to-show fields).
 */
export default defineNuxtPlugin(async () => {
  const config = useRuntimeConfig()
  const settings = usePlatformSettingsStore()

  try {
    const res = await $fetch<{ primary_color: string; platform_name: string; logo_url: string }>(
      `${config.public.apiBase}/platform/settings/public/`
    )
    settings.set(res)
    applyPlatformPrimary(res.primary_color)
  }
  catch {
    // Backend down or migrations not run — fall back to defaults.
  }
})
