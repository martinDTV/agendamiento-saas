/**
 * Server-side no-op registration for the animation directives.
 *
 * The real behavior lives in reveal.client.ts (GSAP, browser-only). During SSR
 * those directives don't exist, which makes Vue warn "Failed to resolve
 * directive". Registering empty directives here silences that without shipping
 * any animation logic to the server. Elements render fully visible by default.
 */
export default defineNuxtPlugin((nuxtApp) => {
  const noop = {}
  const app = nuxtApp.vueApp
  app.directive('reveal', noop)
  app.directive('reveal-stagger', noop)
  app.directive('count', noop)
  app.directive('parallax', noop)
})
